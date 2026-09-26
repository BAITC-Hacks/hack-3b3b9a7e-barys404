"""Expanding-window validation; fixed parameters, no deployment-model mutation.

Run ``python -m ml.validation`` after preparing the real source data.
Only institutional aggregates and metrics are persisted, never patient rows.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
import time

from catboost import CatBoostRegressor
import numpy as np
import pandas as pd

from backend.core import config
from ml import load_forecast as forecast
from backend.data_pipeline.data_loader import source_fingerprint
from ml.feature_engineering import CATEGORICAL_FEATURES, make_features
from ml.train_waiting_model import MODEL_PARAMETERS, regression_metrics
from backend.core.utils import read_json, write_json
from ml.waiting_estimator import VERSION as WAITING_ESTIMATOR_VERSION, calibrated_predictions, fit_calibration

LOGGER = logging.getLogger(__name__)
REPORT_PATH = config.MODELS_DIR / "temporal_validation.json"
VALIDATION_VERSION = 2
FOLDS = 3
WAIT_TEST_DAYS = 14
MIN_GROUP_SIZE = 30


def protocol_signature():
    protocol = {"version": VALIDATION_VERSION, "folds": FOLDS, "wait_days": WAIT_TEST_DAYS,
                "waiting_estimator": WAITING_ESTIMATOR_VERSION,
                "waiting_parameters": MODEL_PARAMETERS, "forecast_parameters": forecast.MODEL_PARAMETERS,
                "forecast_version": forecast.MODEL_VERSION}
    return hashlib.sha256(json.dumps(protocol, sort_keys=True).encode()).hexdigest()


def waiting_fold(frame, test_start, test_end):
    """Only labels known strictly before test_start can enter training."""
    start, end = pd.Timestamp(test_start), pd.Timestamp(test_end)
    if start > end:
        raise ValueError("Test start must not be after its end.")
    registration = pd.to_datetime(frame["registration_dt"])
    hospitalization = pd.to_datetime(frame["hospitalization_dt"])
    eligible = (frame["target_eligible"].fillna(False).astype(bool)
                & frame["wait_days"].between(config.MIN_WAIT_DAYS, config.MAX_WAIT_DAYS)
                & hospitalization.ge(registration) & frame["refusal_dt"].isna())
    early = registration.lt(start)
    train = frame.loc[eligible & early & hospitalization.lt(start)].copy()
    test = frame.loc[eligible & registration.dt.normalize().between(start, end)].copy()
    if train.empty or test.empty:
        raise ValueError("Insufficient eligible train/test observations for temporal validation.")
    return train, test, int((eligible & early & hospitalization.ge(start)).sum())


def error_groups(frame, group, minimum=MIN_GROUP_SIZE):
    """Suppressed small groups; equal weighting per evaluated referral."""
    if minimum < 2:
        raise ValueError("Grouped validation requires at least two observations.")
    work = frame.assign(absolute_error=(frame["actual"] - frame["prediction"]).abs(),
                        squared_error=(frame["actual"] - frame["prediction"]) ** 2,
                        baseline_error=(frame["actual"] - frame["baseline"]).abs())
    grouped = work.groupby(group, dropna=False).agg(
        observations=("actual", "size"), mae=("absolute_error", "mean"),
        mse=("squared_error", "mean"), baseline_mae=("baseline_error", "mean"),
        observed_mean=("actual", "mean"), predicted_mean=("prediction", "mean"))
    grouped = grouped.loc[grouped["observations"] >= minimum].reset_index()
    grouped["rmse"] = np.sqrt(grouped.pop("mse"))
    grouped[group] = grouped[group].fillna("Unknown").astype(str)
    return grouped.sort_values("observations", ascending=False).to_dict(orient="records")


def pooled_metrics(frame):
    mae = float(np.abs(frame["actual"] - frame["prediction"]).mean())
    baseline_mae = float(np.abs(frame["actual"] - frame["baseline"]).mean())
    errors = np.abs(frame["actual"] - frame["prediction"])
    return {"observations": len(frame), "mae": mae,
            "rmse": float(np.sqrt(np.square(frame["actual"] - frame["prediction"]).mean())),
            "baseline_mae": baseline_mae,
            "improvement_pct": 100 * (baseline_mae - mae) / baseline_mae if baseline_mae else None,
            "median_absolute_error": float(errors.quantile(0.5)),
            "p90_absolute_error": float(errors.quantile(0.9))}


def validate_waiting(frame):
    frame = frame.sort_values(["registration_dt", *CATEGORICAL_FEATURES,
                               "hospitalization_dt", "refusal_dt", "wait_days"], kind="stable").reset_index(drop=True)
    last = pd.to_datetime(frame["registration_dt"]).max().normalize()
    folds, predictions = [], []
    for offset in reversed(range(FOLDS)):
        end = last - np.timedelta64(offset * WAIT_TEST_DAYS, "D")
        start = end - np.timedelta64(WAIT_TEST_DAYS - 1, "D")
        train, test, purged = waiting_fold(frame, start, end)
        LOGGER.info("Waiting fold %s..%s: %s train, %s test, %s unavailable labels purged",
                    start.date(), end.date(), len(train), len(test), purged)
        model = CatBoostRegressor(**MODEL_PARAMETERS)
        model.fit(make_features(train), train["wait_days"], cat_features=CATEGORICAL_FEATURES)
        predicted, _, _ = calibrated_predictions(make_features(test), model.predict(make_features(test)),
                                                  fit_calibration(make_features(train), train["wait_days"]))
        median = float(train["wait_days"].median())
        fold = {"test_start": start.date().isoformat(), "test_end": end.date().isoformat(),
                "train_rows": len(train), "test_rows": len(test), "purged_labels": purged,
                "train_last_label": train["hospitalization_dt"].max().isoformat(),
                **regression_metrics(test["wait_days"], predicted, median)}
        folds.append(fold)
        part = test[["region_origin_code", "hospital_mo", "bed_profile"]].copy()
        part["actual"], part["prediction"], part["baseline"] = test["wait_days"], predicted, median
        predictions.append(part)
        LOGGER.info("Waiting fold MAE %.4f; baseline %.4f", fold["mae"], fold["baseline_mae"])
    scored = pd.concat(predictions, ignore_index=True)
    return {"folds": folds, "pooled": pooled_metrics(scored),
            "groups": {group: error_groups(scored, group) for group in ("region_origin_code", "hospital_mo", "bed_profile")},
            "minimum_group_size": MIN_GROUP_SIZE,
            "evaluation_scope": "Observed eligible 0-90 day hospitalizations; test outcomes can be learned after the test registration window. Not all referred patients."}


def validate_forecast(daily):
    last = pd.to_datetime(daily["date"]).max()
    folds, predictions = [], []
    for offset in reversed(range(FOLDS)):
        end = last - np.timedelta64(offset * forecast.HORIZON_DAYS, "D")
        train, test, split = forecast.temporal_holdout(daily.loc[daily["date"] <= end])
        LOGGER.info("Forecast fold %s..%s: %s train, %s test", split["test_start"], split["test_end"], len(train), len(test))
        model = CatBoostRegressor(**forecast.MODEL_PARAMETERS)
        model.fit(train[forecast.FEATURE_COLUMNS], train["target"], cat_features=["hospital_mo"])
        predicted = np.maximum(0, model.predict(test[forecast.FEATURE_COLUMNS]))
        metrics = forecast._metrics(test["target"], predicted, test["mean_7"], test["seasonal_baseline"])
        folds.append({**split, "train_rows": len(train), "test_rows": len(test), **metrics})
        predictions.append(test[["hospital_mo", "horizon"]].assign(
            actual=test["target"], prediction=predicted, baseline=test["mean_7"], seasonal=test["seasonal_baseline"]))
        LOGGER.info("Forecast fold MAE %.4f; mean baseline %.4f; seasonal baseline %.4f",
                    metrics["mae"], metrics["baseline_mae"], metrics["seasonal_baseline_mae"])
    scored = pd.concat(predictions, ignore_index=True)
    metrics = pooled_metrics(scored)
    metrics["seasonal_baseline_mae"] = float(np.abs(scored["actual"] - scored["seasonal"]).mean())
    return {"folds": folds, "pooled": metrics,
            "by_horizon": [{"horizon": int(h), **pooled_metrics(rows),
                            "seasonal_baseline_mae": float(np.abs(rows["actual"] - rows["seasonal"]).mean())}
                           for h, rows in scored.groupby("horizon")],
            "evaluation_scope": "Equal weighting per hospital/day; direct seven-day forecasts from fixed end-of-day origins."}


def validation_status():
    try:
        report = read_json(REPORT_PATH)
        quality = read_json(config.QUALITY_PATH)
        current = source_fingerprint()
        if (not quality.get("pipeline_complete") or report.get("source_fingerprint") != current
                or quality.get("source_fingerprint") != current or report.get("protocol_signature") != protocol_signature()):
            return {"available": False, "reason": "Validation belongs to a different data or protocol version."}
        return {"available": True, "report": report}
    except (OSError, ValueError, AttributeError):
        return {"available": False, "reason": "Multi-period validation has not been completed for this dataset."}


def run_validation(force=False):
    if not force:
        previous = validation_status()
        if previous["available"]:
            LOGGER.info("Temporal validation is up to date.")
            return previous["report"]
    quality = forecast._prepared_report()
    started = time.monotonic()
    columns = CATEGORICAL_FEATURES + ["region_origin_code", "registration_dt", "hospitalization_dt", "refusal_dt", "wait_days", "target_eligible"]
    waiting = validate_waiting(pd.read_parquet(config.ANALYTICAL_PATH, columns=columns))
    referral_load = validate_forecast(pd.read_parquet(config.PROCESSED_DIR / "hospital_day.parquet",
                                                    columns=["hospital_mo", "date", "referrals"]))
    if forecast._prepared_report()["source_fingerprint"] != quality["source_fingerprint"]:
        raise ValueError("Sources changed during validation; rerun on a stable dataset.")
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "source_fingerprint": quality["source_fingerprint"],
              "validation_version": VALIDATION_VERSION, "protocol_signature": protocol_signature(),
              "parameters_selected_on_test": False, "deployment_models_modified": False,
              "estimator_selection_overlap": "Waiting estimator selection used an internal pre-March-14 chronological validation subset. Earlier folds overlap that selection history; report is exploratory rather than independent confirmation of the selected rule.",
              "waiting": waiting, "forecast": referral_load, "seconds": round(time.monotonic() - started, 2),
              "limitations": ["Only 90 historical registration days are available in the current extract.",
                              "Expanding training windows, disjoint test windows; later folds may learn outcomes from earlier folds only once available.",
                              "Retrospective exports do not establish historical data-arrival times or revisions.",
                              "Error quantiles are descriptive held-out errors, not prediction intervals or coverage guarantees.",
                              "Fixed hyperparameters per fold; earlier waiting folds overlap estimator-selection data. These results do not validate live deployment or clinical decisions."]}
    write_json(REPORT_PATH, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = run_validation(force=args.force)
    print(json.dumps({name: result[name]["pooled"] for name in ("waiting", "forecast")}, indent=2))
