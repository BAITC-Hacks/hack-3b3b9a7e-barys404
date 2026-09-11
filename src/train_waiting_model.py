"""Train and evaluate a real CatBoost waiting-time model on a temporal holdout.

Run ``python -m src.train_waiting_model`` after adding source CSVs to data/.
Test observations are never used for fitting, early stopping, or configuration.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import logging
import math
import os
from pathlib import Path
import time

from catboost import CatBoostRegressor
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src import config
from src.feature_engineering import CATEGORICAL_FEATURES, FEATURE_COLUMNS, category_options, make_features
from src.utils import write_json

LOGGER = logging.getLogger(__name__)
MODEL_VERSION = "waiting-catboost-temporal-v2"
MODEL_PARAMETERS = {
    "iterations": 300,
    "depth": 6,
    "learning_rate": 0.06,
    "loss_function": "MAE",
    "random_seed": config.RANDOM_SEED,
    "thread_count": config.THREAD_COUNT,
    "allow_writing_files": False,
    "verbose": False,
}


def chronological_split(frame: pd.DataFrame, train_fraction: float = config.TRAIN_FRACTION):
    """Split whole registration dates, then select labels known at train cutoff.

    The boundary uses *all* valid registration dates, before outcome filtering.
    An early referral hospitalized on/after the first test date is purged from
    train: its label would have been unknown when the test period began.
    """
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1.")
    required = {"registration_dt", "hospitalization_dt", "wait_days", "target_eligible"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Analytical dataset is missing columns: {sorted(missing)}")
    registration = pd.to_datetime(frame["registration_dt"], errors="coerce", format="mixed")
    hospitalization = pd.to_datetime(frame["hospitalization_dt"], errors="coerce", format="mixed")
    days = registration.dt.normalize()
    unique_days = sorted(days.dropna().unique())
    if len(unique_days) < 2:
        raise ValueError("At least two distinct valid registration dates are required for a time split.")
    boundary_index = max(1, min(len(unique_days) - 1, math.floor(len(unique_days) * train_fraction)))
    cutoff = pd.Timestamp(unique_days[boundary_index])
    target = pd.to_numeric(frame["wait_days"], errors="coerce")
    eligible = (
        frame["target_eligible"].fillna(False).astype(bool)
        & target.between(config.MIN_WAIT_DAYS, config.MAX_WAIT_DAYS)
        & hospitalization.notna()
        & hospitalization.ge(registration)
    )
    if "refusal_dt" in frame:
        # Defensive duplicate protection: contradictory outcomes never train.
        eligible &= pd.to_datetime(frame["refusal_dt"], errors="coerce", format="mixed").isna()
    early = days.lt(cutoff)
    late = days.ge(cutoff)
    purged = early & eligible & hospitalization.ge(cutoff)
    train_mask = early & eligible & hospitalization.lt(cutoff)
    test_mask = late & eligible
    train = frame.loc[train_mask].copy()
    test = frame.loc[test_mask].copy()
    train["wait_days"] = target.loc[train_mask]
    test["wait_days"] = target.loc[test_mask]
    if train.empty or test.empty:
        raise ValueError("No eligible train or test rows remain after temporal split and outcome-time purge.")
    details = {
        "method": "chronological_unique_registration_dates_then_label_availability_purge",
        "train_fraction_dates_requested": train_fraction,
        "registration_dates_total": len(unique_days),
        "registration_dates_train_window": boundary_index,
        "registration_dates_test_window": len(unique_days) - boundary_index,
        "test_start": cutoff.isoformat(),
        "train_window_start": pd.Timestamp(unique_days[0]).isoformat(),
        "train_window_end": pd.Timestamp(unique_days[boundary_index - 1]).isoformat(),
        "test_window_end": pd.Timestamp(unique_days[-1]).isoformat(),
        "train_label_cutoff_exclusive": cutoff.isoformat(),
        "test_used_for_early_stopping": False,
        "test_used_for_parameter_selection": False,
        "exclusions": {
            "invalid_registration": int(registration.isna().sum()),
            "early_rows_without_eligible_target": int((early & ~eligible).sum()),
            "early_labels_unavailable_at_cutoff": int(purged.sum()),
            "late_rows_without_eligible_target": int((late & ~eligible).sum()),
        },
    }
    return train, test, details


def regression_metrics(actual, predicted, median_prediction: float) -> dict:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    baseline = np.full(actual.shape, median_prediction, dtype=float)
    mae = float(mean_absolute_error(actual, predicted))
    baseline_mae = float(mean_absolute_error(actual, baseline))
    return {
        "mae": mae,
        "rmse": float(math.sqrt(mean_squared_error(actual, predicted))),
        "baseline_mae": baseline_mae,
        "baseline_rmse": float(math.sqrt(mean_squared_error(actual, baseline))),
        "improvement_pct": float(100 * (baseline_mae - mae) / baseline_mae) if baseline_mae else None,
        "baseline_median_days": float(median_prediction),
    }


def aggregate_predictions(actual, predicted, minimum_group_size: int = 10) -> list[dict]:
    """Aggregate test performance by wait band without exporting patient rows."""
    if minimum_group_size < 2:
        raise ValueError("Prediction aggregates require groups of at least two observations.")
    points = pd.DataFrame({"actual": np.asarray(actual), "predicted": np.asarray(predicted)})
    edges = [-np.inf, 1, 3, 7, 14, 30, 60, np.inf]
    labels = ["0–1 days", "1–3 days", "3–7 days", "7–14 days", "14–30 days", "30–60 days", "60–90 days"]
    points["actual_bin"] = pd.cut(points["actual"], edges, labels=labels, right=False)
    grouped = points.groupby("actual_bin", observed=True).agg(
        count=("actual", "size"), actual_mean=("actual", "mean"), predicted_mean=("predicted", "mean")
    ).reset_index()
    grouped = grouped.loc[grouped["count"].ge(minimum_group_size)]
    grouped["actual_bin"] = grouped["actual_bin"].astype(str)
    return grouped.to_dict(orient="records")


def _period(frame: pd.DataFrame) -> dict:
    dates = pd.to_datetime(frame["registration_dt"])
    return {"start": dates.min().isoformat(), "end": dates.max().isoformat()}


def train_model(force_preprocess: bool = False) -> dict:
    """Rebuild stale processed data, fit once, and persist auditable artifacts."""
    from src.preprocessing import run_pipeline

    started = time.monotonic()
    config.ensure_directories()
    report = run_pipeline(force=force_preprocess)
    columns = CATEGORICAL_FEATURES + ["registration_dt", "hospitalization_dt", "refusal_dt", "wait_days", "target_eligible"]
    # Parquet column projection avoids loading diagnoses, identifiers or raw CSVs.
    frame = pd.read_parquet(config.ANALYTICAL_PATH, columns=columns)
    # SQL hash joins/DISTINCT can emit different physical row orders between
    # identical rebuilds. Fix the order before CatBoost's seeded permutations.
    frame = frame.sort_values(
        ["registration_dt", *CATEGORICAL_FEATURES, "hospitalization_dt", "refusal_dt", "wait_days"],
        kind="stable", na_position="last",
    ).reset_index(drop=True)
    train, test, split = chronological_split(frame)
    LOGGER.info("Time split: %s train, %s test; exclusions=%s", len(train), len(test), split["exclusions"])
    x_train = make_features(train)
    x_test = make_features(test)
    y_train = train["wait_days"].to_numpy(dtype=float)
    y_test = test["wait_days"].to_numpy(dtype=float)
    model = CatBoostRegressor(**MODEL_PARAMETERS)
    LOGGER.info("Training CatBoost on %s rows; test is untouched by fitting.", len(train))
    model.fit(x_train, y_train, cat_features=CATEGORICAL_FEATURES)
    # The same nonnegative post-processing is applied in predict.py.
    prediction = np.maximum(0.0, model.predict(x_test))
    metrics = regression_metrics(y_test, prediction, float(np.median(y_train)))
    importance = sorted(
        [{"feature": feature, "importance": float(value)} for feature, value in zip(FEATURE_COLUMNS, model.feature_importances_)],
        key=lambda row: row["importance"], reverse=True,
    )
    aggregated = aggregate_predictions(y_test, prediction)
    metadata = {
        "model_version": MODEL_VERSION,
        "model_type": "CatBoostRegressor",
        "training_date": datetime.now(timezone.utc).isoformat(),
        "source_fingerprint": report.get("source_fingerprint"),
        "source_coverage": report.get("coverage", report.get("source_files", {})),
        "model_parameters": MODEL_PARAMETERS,
        "training_order": "stable registration timestamp, categorical features, outcome timestamps, wait_days",
        "target": "hospitalization_dt - registration_dt, in fractional days",
        "estimand": f"conditional median among observed hospitalizations with cleaned wait between {config.MIN_WAIT_DAYS:g} and {config.MAX_WAIT_DAYS:g} days",
        "target_bounds_days": {"min": config.MIN_WAIT_DAYS, "max": config.MAX_WAIT_DAYS},
        "features": FEATURE_COLUMNS,
        "categorical_features": CATEGORICAL_FEATURES,
        "feature_options": category_options(x_train),
        "excluded_predictors": ["hospitalization_code", "patient_seq_no", "hospitalization_dt", "refusal_dt", "planned_dt", "sdu_load_date", "outcome", "wait_days", "future_aggregates", "treated_cases_2026"],
        "rows": {"analytical": len(frame), "train": len(train), "test": len(test), "excluded_from_model": len(frame) - len(train) - len(test)},
        "train_period": _period(train),
        "test_period": _period(test),
        "split": split,
        "pipeline_target_exclusions": report.get("cleaning", report.get("target_exclusions", {})),
        "pipeline_outcome_summary": report.get("summary", {}),
        "source_referral_date_quality": report.get("datasets", {}).get("referrals", {}).get("dates", {}),
        "cleaning_policy": report.get("policy", {}),
        "metrics": metrics,
        "feature_importance": importance,
        "actual_vs_predicted": aggregated,
        "actual_vs_predicted_min_group_size": 10,
        "actual_vs_predicted_suppressed_rows": len(test) - sum(row["count"] for row in aggregated),
        "prediction_postprocessing": "clip negative predictions to zero; identical during evaluation and inference",
        "training_seconds": round(time.monotonic() - started, 2),
        "limitations": [
            "Initial ML baseline — Work in Progress; an operational decision-support estimate, not a clinical recommendation.",
            "Only supplied CSV parts are represented; this is not a complete national cohort.",
            "Trained and evaluated only on observed hospitalizations with eligible 0–90 day waits. Refusals and unresolved outcomes are excluded: this creates selection bias and right-censoring, especially near the end of follow-up.",
            "MAE loss estimates the conditional median (typical wait), not the mathematical expected wait or remaining waiting time of a current queue.",
            "Training labels recorded on or after the test boundary are purged; no features from future outcomes or 2026 treated-case aggregates are used.",
            "One chronological holdout is an initial estimate, without confidence intervals, external validation, or hyperparameter tuning on the test set.",
            "Short historical coverage does not validate deployment in 2026 or reliable 30/90-day hospital-load forecasts.",
            "Feature importance is model association, not causality; rare and unseen categories may be unreliable.",
            "Actual-versus-predicted points represent wait-band means; individual errors are summarized separately by MAE and RMSE.",
        ],
    }
    temporary = Path(config.MODEL_PATH).with_suffix(".cbm.tmp")
    model.save_model(str(temporary), format="cbm")
    os.replace(temporary, config.MODEL_PATH)
    write_json(config.METADATA_PATH, metadata)
    LOGGER.info("Saved %s and %s", config.MODEL_PATH, config.METADATA_PATH)
    LOGGER.info("Holdout MAE=%.4f days; RMSE=%.4f; median baseline MAE=%.4f; improvement=%s%%", metrics["mae"], metrics["rmse"], metrics["baseline_mae"], metrics["improvement_pct"])
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force-preprocess", action="store_true", help="Rebuild processed Parquet even if source fingerprint is unchanged.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        train_model(force_preprocess=args.force_preprocess)
    except (FileNotFoundError, ValueError) as exc:
        parser.exit(1, f"Training could not proceed: {exc}\n")


if __name__ == "__main__":
    main()
