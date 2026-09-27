"""Direct seven-day incoming-referral forecasts with a fixed-origin holdout.

An origin is the END of an observed day. All seven predictions use the same
28-day observed history, including that day; no holdout observations become
features. The persisted model is the evaluated model (no refit on the test).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from catboost import CatBoostRegressor
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from backend.core.config import MODELS_DIR, PROCESSED_DIR, QUALITY_PATH, THREAD_COUNT
from backend.data_pipeline.data_loader import source_fingerprint
from backend.core.utils import read_json, write_json


LOGGER = logging.getLogger(__name__)
MODEL_VERSION = 2
HORIZON_DAYS = 7
MIN_HISTORY_DAYS = 28
MIN_EVALUATION_DAYS = MIN_HISTORY_DAYS + 2 * HORIZON_DAYS
FEATURE_COLUMNS = [
    "hospital_mo", "horizon", "target_day_of_week", "lag_1", "lag_7",
    "lag_14", "mean_7", "mean_14", "mean_28",
]
MODEL_PARAMETERS = dict(iterations=300, depth=6, learning_rate=0.06,
                        loss_function="MAE", random_seed=42, verbose=False,
                        thread_count=THREAD_COUNT, allow_writing_files=False)
MODEL_PATH = MODELS_DIR / "referral_load_7day_catboost.cbm"
METADATA_PATH = MODELS_DIR / "referral_load_7day_metadata.json"


def _file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _normalise(frame: pd.DataFrame) -> pd.DataFrame:
    required = ["hospital_mo", "date", "referrals"]
    missing = set(required).difference(frame.columns)
    if missing:
        raise ValueError(f"Hospital/day data is missing columns: {', '.join(sorted(missing))}")
    result = frame.loc[:, required].copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result["referrals"] = pd.to_numeric(result["referrals"], errors="coerce")
    if result.empty or result.isna().any().any():
        raise ValueError("Hospital/day data must be nonempty and contain no missing or invalid values.")
    if not np.isfinite(result["referrals"]).all() or (result["referrals"] < 0).any():
        raise ValueError("Referral counts must be finite and nonnegative.")
    if not result["date"].eq(result["date"].dt.normalize()).all():
        raise ValueError("Hospital/day dates must be calendar days, without times.")
    result["hospital_mo"] = result["hospital_mo"].astype(str)
    if result["hospital_mo"].str.strip().eq("").any():
        raise ValueError("Hospital names must not be empty.")
    if result.duplicated(["hospital_mo", "date"]).any():
        raise ValueError("Duplicate hospital/day rows must be resolved before forecasting.")
    result = result.sort_values(["hospital_mo", "date"], kind="stable").reset_index(drop=True)
    gaps = result.groupby("hospital_mo", sort=False)["date"].diff().dropna()
    if not gaps.eq(np.timedelta64(1, "D")).all():
        raise ValueError("Forecasting requires a dense daily calendar; missing days are not silently filled.")
    result["referrals"] = result["referrals"].astype(float)
    return result


def _base_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Vectorized trailing windows include the last observed day (the origin)."""
    rows = frame.rename(columns={"date": "origin"}).copy()
    grouped = rows.groupby("hospital_mo", sort=False)["referrals"]
    rows["lag_1"] = rows["referrals"]
    rows["lag_7"] = grouped.shift(6)
    rows["lag_14"] = grouped.shift(13)
    for days in (7, 14, 28):
        rows[f"mean_{days}"] = grouped.transform(lambda values: values.rolling(days, min_periods=days).mean())
    return rows


def _horizon_rows(base: pd.DataFrame, horizon: int) -> pd.DataFrame:
    rows = base.drop(columns="referrals").copy()
    rows["horizon"] = horizon
    rows["target_date"] = rows["origin"] + np.timedelta64(horizon, "D")
    rows["target_day_of_week"] = rows["target_date"].dt.dayofweek
    return rows


def make_training_rows(frame: pd.DataFrame, target_before: pd.Timestamp | None = None) -> pd.DataFrame:
    """Direct h=1..7 examples, with labels strictly earlier than target_before."""
    frame = _normalise(frame)
    if target_before is not None:
        frame = frame.loc[frame["date"] < pd.Timestamp(target_before)].copy()
    base = _base_features(frame)
    grouped = frame.groupby("hospital_mo", sort=False)["referrals"]
    pieces = []
    for horizon in range(1, HORIZON_DAYS + 1):
        rows = _horizon_rows(base, horizon)
        rows["target"] = grouped.shift(-horizon)
        rows["seasonal_baseline"] = grouped.shift(HORIZON_DAYS - horizon)
        pieces.append(rows.dropna(subset=["mean_28", "target"]))
    return pd.concat(pieces, ignore_index=True).sort_values(
        ["hospital_mo", "origin", "horizon"], kind="stable").reset_index(drop=True)


def make_forecast_rows(frame: pd.DataFrame, origin: pd.Timestamp) -> pd.DataFrame:
    """Create seven forecasts per hospital using only observations <= origin."""
    frame = _normalise(frame)
    origin = pd.Timestamp(origin)
    history = frame.loc[frame["date"] <= origin].copy()
    base = _base_features(history)
    grouped = history.groupby("hospital_mo", sort=False)["referrals"]
    pieces = []
    for horizon in range(1, HORIZON_DAYS + 1):
        rows = _horizon_rows(base, horizon)
        rows["seasonal_baseline"] = grouped.shift(HORIZON_DAYS - horizon)
        pieces.append(rows.loc[rows["origin"].eq(origin) & rows["mean_28"].notna()])
    return pd.concat(pieces, ignore_index=True).sort_values(
        ["hospital_mo", "horizon"], kind="stable").reset_index(drop=True)


def temporal_holdout(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Train on known labels, then predict the entire last week from one origin."""
    frame = _normalise(frame)
    final_date = frame["date"].max()
    origin = final_date - np.timedelta64(HORIZON_DAYS, "D")
    if frame["date"].nunique() < MIN_EVALUATION_DAYS:
        raise ValueError(f"At least {MIN_EVALUATION_DAYS} calendar days are required for training and a seven-day holdout.")
    train = make_training_rows(frame, target_before=origin + np.timedelta64(1, "D"))
    horizons_per_hospital = train.groupby("hospital_mo")["horizon"].nunique()
    trained_hospitals = horizons_per_hospital.index[horizons_per_hospital.eq(HORIZON_DAYS)]
    train = train.loc[train["hospital_mo"].isin(trained_hospitals)].reset_index(drop=True)
    test = make_forecast_rows(frame, origin)
    test = test.merge(frame.rename(columns={"date": "target_date", "referrals": "target"}),
                      on=["hospital_mo", "target_date"], how="left", validate="one_to_one")
    complete = test.groupby("hospital_mo")["target"].count()
    scored_hospitals = complete.index[complete.eq(HORIZON_DAYS)].intersection(trained_hospitals)
    test = test.loc[test["hospital_mo"].isin(scored_hospitals)].reset_index(drop=True)
    if train.empty or test.empty:
        raise ValueError("No hospitals have enough training history and a complete seven-day holdout.")
    split = {
        "method": "single fixed end-of-day origin; seven direct horizons; no holdout updates",
        "forecast_origin": origin.isoformat(),
        "train_last_target": train["target_date"].max().isoformat(),
        "test_start": (origin + np.timedelta64(1, "D")).isoformat(), "test_end": final_date.isoformat(),
        "test_hospitals": len(scored_hospitals),
        "excluded_test_hospitals": int(frame["hospital_mo"].nunique() - len(scored_hospitals)),
        "refit_on_holdout": False,
    }
    return train, test, split


def _metrics(actual, predicted, baseline, seasonal) -> dict:
    mae = float(mean_absolute_error(actual, predicted))
    baseline_mae = float(mean_absolute_error(actual, baseline))
    return {
        "mae": mae, "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "baseline_mae": baseline_mae,
        "seasonal_baseline_mae": float(mean_absolute_error(actual, seasonal)),
        "improvement_pct": 100 * (baseline_mae - mae) / baseline_mae if baseline_mae else None,
    }


def _prepared_report() -> dict:
    if not QUALITY_PATH.exists():
        raise FileNotFoundError("Data-quality report is missing. Run data preparation first.")
    report = read_json(QUALITY_PATH)
    if not isinstance(report, dict) or not report.get("pipeline_complete") or report.get("source_fingerprint") != source_fingerprint():
        raise ValueError("Source data changed or preparation is incomplete. Refresh data before forecasting.")
    return report


def train_load_forecast(hospital_day_path: Path | None = None, model_path: Path | None = None,
                        metadata_path: Path | None = None, fingerprint: str | None = None) -> dict:
    """Fit once and persist the evaluated model, aggregate predictions and metrics.

    Explicit custom data paths and fingerprints support isolated offline fixtures;
    production training always requires a completed, current preparation report.
    """
    started = time.monotonic()
    report = _prepared_report() if hospital_day_path is None or fingerprint is None else {}
    fingerprint = report.get("source_fingerprint", fingerprint)
    hospital_day_path = Path(hospital_day_path or PROCESSED_DIR / "hospital_day.parquet")
    model_path, metadata_path = Path(model_path or MODEL_PATH), Path(metadata_path or METADATA_PATH)
    source_hash = _file_hash(hospital_day_path)
    frame = _normalise(pd.read_parquet(hospital_day_path, columns=["hospital_mo", "date", "referrals"]))
    train, test, split = temporal_holdout(frame)
    LOGGER.info("Fixed-origin split: %s train, %s test, origin=%s", len(train), len(test), split["forecast_origin"])
    model = CatBoostRegressor(**MODEL_PARAMETERS)
    model.fit(train[FEATURE_COLUMNS], train["target"], cat_features=["hospital_mo"])
    test["predicted_referrals"] = np.maximum(0.0, np.asarray(model.predict(test[FEATURE_COLUMNS]), dtype=float))
    metrics = _metrics(test["target"], test["predicted_referrals"], test["mean_7"], test["seasonal_baseline"])
    by_horizon = [{"horizon": int(h), "rows": len(rows), **_metrics(
        rows["target"], rows["predicted_referrals"], rows["mean_7"], rows["seasonal_baseline"])}
        for h, rows in test.groupby("horizon")]
    if source_hash != _file_hash(hospital_day_path) or (report and _prepared_report()["source_fingerprint"] != fingerprint):
        raise ValueError("Data changed during training. Retry with a stable prepared dataset.")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = model_path.with_suffix(".cbm.tmp")
    model.save_model(str(temporary), format="cbm")
    os.replace(temporary, model_path)
    validation_path = model_path.with_suffix(".validation.parquet")
    test.to_parquet(validation_path, index=False)
    metadata = {
        "model_version": MODEL_VERSION, "model_type": "CatBoostRegressor",
        "training_date": datetime.now(timezone.utc).isoformat(),
        "forecast_target": "daily referral count received by hospital", "horizon_days": HORIZON_DAYS,
        "source_fingerprint": fingerprint, "source_coverage": report.get("coverage", {}),
        "hospital_day_sha256": source_hash, "model_sha256": _file_hash(model_path),
        "history_start": frame["date"].min().isoformat(), "history_end": frame["date"].max().isoformat(),
        "test_period": {"start": split["test_start"], "end": split["test_end"]}, "split": split,
        "rows": {"train": len(train), "test": len(test), "hospitals": int(frame["hospital_mo"].nunique())},
        "metrics": metrics, "metrics_by_horizon": by_horizon, "features": FEATURE_COLUMNS,
        "model_parameters": MODEL_PARAMETERS, "validation_predictions": validation_path.name,
        "feature_timing": "Origin is end of day; lag_1 is origin, lag_7 is origin-6, lag_14 is origin-13; all rolling means include origin.",
        "baselines": {"primary": "Mean of seven observed days ending at origin, repeated for all horizons",
                      "seasonal": "Observed count on target weekday in the preceding week (target_date - 7 days)"},
        "training_seconds": round(time.monotonic() - started, 2),
        "limitations": [
            "Prototype forecasts referrals received, not occupied beds, capacity, staffing, admissions or a live waiting list.",
            "Only supplied historical source parts are represented. Zero calendar days mean no records in those files.",
            "One fixed-origin historical holdout; multiple temporal backtests and external validation are still required.",
            "The evaluated model is saved without refitting on the holdout; inference can use the latest observed history.",
            "Dates are registration dates in a retrospective extract; historical ingestion delays and revisions are unknown.",
            "The next week follows the last supplied observation, not today's calendar date.",
        ],
    }
    write_json(metadata_path, metadata)
    LOGGER.info("Forecast metrics: %s", metrics)
    return metadata


def forecast_status(report: dict | None = None, hospital_day_path: Path | None = None) -> dict:
    unavailable = {"available": False, "stale": True,
                   "reason": "Forecast artifacts or source data changed. Refresh data and retrain the forecast."}
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        return {"available": False, "stale": False, "reason": "No 7-day referral-load model has been trained."}
    try:
        metadata = read_json(METADATA_PATH)
        if not isinstance(metadata, dict):
            return unavailable
        current = _prepared_report()
        if report is not None and (not report.get("pipeline_complete") or report.get("source_fingerprint") != current["source_fingerprint"]):
            return unavailable
        path = Path(hospital_day_path or PROCESSED_DIR / "hospital_day.parquet")
        if (metadata.get("model_version") != MODEL_VERSION
                or metadata.get("source_fingerprint") != current["source_fingerprint"]
                or metadata.get("hospital_day_sha256") != _file_hash(path)
                or metadata.get("model_sha256") != _file_hash(MODEL_PATH)):
            return unavailable
    except (OSError, ValueError, KeyError, TypeError):
        return unavailable
    return {"available": True, "stale": False, "reason": "Forecast model ready."}


def _forecast_context(hospital: str, hospital_day_path: Path | None = None):
    status = forecast_status(hospital_day_path=hospital_day_path)
    if not status["available"]:
        raise FileNotFoundError(status["reason"])
    frame = _normalise(pd.read_parquet(hospital_day_path or PROCESSED_DIR / "hospital_day.parquet",
                                      columns=["hospital_mo", "date", "referrals"]))
    history = frame.loc[frame["hospital_mo"].eq(str(hospital))]
    origin = frame["date"].max()
    if len(history) < MIN_HISTORY_DAYS or history["date"].max() != origin:
        raise ValueError("This hospital needs 28 consecutive days through the latest observed date.")
    features = make_forecast_rows(history, origin)
    model = CatBoostRegressor()
    model.load_model(str(MODEL_PATH), format="cbm")
    return model, features


def forecast_next_week(hospital: str, hospital_day_path: Path | None = None) -> pd.DataFrame:
    """Seven direct predictions from one fixed end-of-day observed origin."""
    model, features = _forecast_context(hospital, hospital_day_path)
    prediction = np.asarray(model.predict(features[FEATURE_COLUMNS]), dtype=float)
    if not np.isfinite(prediction).all():
        raise ValueError("Forecast returned a non-finite estimate.")
    return pd.DataFrame({"date": features["target_date"], "predicted_referrals": np.maximum(0.0, prediction)})


def explain_next_week(hospital: str, horizon: int = 1, hospital_day_path: Path | None = None) -> dict:
    from ml.explanations import explain_model
    if horizon not in range(1, HORIZON_DAYS + 1):
        raise ValueError("Choose a forecast horizon from 1 through 7.")
    model, features = _forecast_context(hospital, hospital_day_path)
    selected = features.loc[features["horizon"].eq(horizon), FEATURE_COLUMNS]
    return explain_model(model, selected, ["hospital_mo"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = train_load_forecast()
    print(json.dumps({"metrics": result["metrics"], "rows": result["rows"], "split": result["split"]}, indent=2))
