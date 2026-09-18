"""Train and serve a bounded seven-day referral-volume forecast prototype.

The target is daily *referrals received*, not beds occupied or the current
waiting list.  Features are calculated from observations available at the
forecast origin only, so the held-out final seven days are never used to build
training features.
"""
from __future__ import annotations

import math
import os
from datetime import timedelta
from pathlib import Path

from catboost import CatBoostRegressor
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.config import MODELS_DIR, PROCESSED_DIR
from src.data_loader import source_fingerprint
from src.utils import read_json, write_json


HORIZON_DAYS = 7
MIN_HISTORY_DAYS = 28
FEATURE_COLUMNS = [
    "hospital_mo", "horizon", "target_day_of_week", "lag_1", "lag_7",
    "lag_14", "mean_7", "mean_14", "mean_28",
]
MODEL_PATH = MODELS_DIR / "referral_load_7day_catboost.cbm"
METADATA_PATH = MODELS_DIR / "referral_load_7day_metadata.json"


def _normalise(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"hospital_mo", "date", "referrals"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Hospital/day data is missing columns: {', '.join(sorted(missing))}")
    result = frame.loc[:, ["hospital_mo", "date", "referrals"]].copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce").dt.normalize()
    result["referrals"] = pd.to_numeric(result["referrals"], errors="coerce")
    result = result.dropna(subset=["hospital_mo", "date", "referrals"])
    result["hospital_mo"] = result["hospital_mo"].astype(str)
    result["referrals"] = result["referrals"].clip(lower=0).astype(float)
    return result.sort_values(["hospital_mo", "date"]).drop_duplicates(["hospital_mo", "date"], keep="last")


def _features_from_values(hospital: str, values: dict, origin: pd.Timestamp, horizon: int) -> dict:
    window = lambda days: [float(values.get(origin - pd.DateOffset(days=day), 0.0)) for day in range(1, days + 1)]
    last_7, last_14, last_28 = window(7), window(14), window(28)
    target = origin + pd.DateOffset(days=int(horizon))
    return {
        "hospital_mo": hospital, "horizon": horizon,
        "target_day_of_week": int(target.dayofweek), "lag_1": last_7[0],
        "lag_7": last_7[6], "lag_14": last_14[13], "mean_7": float(np.mean(last_7)),
        "mean_14": float(np.mean(last_14)), "mean_28": float(np.mean(last_28)),
    }


def _features_at(history: pd.DataFrame, origin: pd.Timestamp, horizon: int) -> dict:
    values = dict(zip(history["date"], history["referrals"]))
    return _features_from_values(str(history["hospital_mo"].iloc[0]), values, origin, horizon)


def make_training_rows(frame: pd.DataFrame, target_before: pd.Timestamp | None = None) -> pd.DataFrame:
    """Create direct h=1..7 examples using only completed calendar history."""
    rows = []
    for _, hospital in frame.groupby("hospital_mo", sort=False):
        hospital = hospital.sort_values("date").reset_index(drop=True)
        hospital_name = str(hospital.loc[0, "hospital_mo"])
        values = dict(zip(hospital["date"], hospital["referrals"]))
        dates = set(hospital["date"])
        for index in range(MIN_HISTORY_DAYS, len(hospital)):
            origin = hospital.loc[index, "date"]
            for horizon in range(1, HORIZON_DAYS + 1):
                target = origin + pd.DateOffset(days=int(horizon))
                if target not in dates or (target_before is not None and target >= target_before):
                    continue
                feature = _features_from_values(hospital_name, values, origin, horizon)
                feature["target"] = float(values[target])
                feature["origin"] = origin
                feature["target_date"] = target
                rows.append(feature)
    return pd.DataFrame(rows)


def _model() -> CatBoostRegressor:
    return CatBoostRegressor(iterations=300, depth=6, learning_rate=0.06, loss_function="MAE", random_seed=42, verbose=False)


def train_load_forecast(hospital_day_path: Path | None = None, model_path: Path | None = None,
                        metadata_path: Path | None = None, fingerprint: str | None = None) -> dict:
    """Fit a global hospital/day model and evaluate the final seven observed days."""
    hospital_day_path = Path(hospital_day_path or PROCESSED_DIR / "hospital_day.parquet")
    model_path, metadata_path = Path(model_path or MODEL_PATH), Path(metadata_path or METADATA_PATH)
    if not hospital_day_path.exists():
        raise FileNotFoundError("Hospital/day aggregation is missing. Run data preparation first.")
    frame = _normalise(pd.read_parquet(hospital_day_path))
    if frame.empty:
        raise ValueError("Hospital/day aggregation contains no forecastable records.")
    final_date = frame["date"].max()
    test_start = final_date - pd.DateOffset(days=int(HORIZON_DAYS - 1))
    train = make_training_rows(frame, target_before=test_start)
    test = make_training_rows(frame)
    test = test.loc[(test["target_date"] >= test_start) & (test["target_date"] <= final_date)]
    if train.empty or test.empty:
        raise ValueError("At least 35 calendar days of hospital history are required for the seven-day forecast prototype.")
    x_train, x_test = train[FEATURE_COLUMNS], test[FEATURE_COLUMNS]
    model = _model()
    model.fit(x_train, train["target"], cat_features=["hospital_mo"])
    predicted = np.maximum(0.0, np.asarray(model.predict(x_test), dtype=float))
    baseline = test["mean_7"].to_numpy(dtype=float)
    metrics = {
        "mae": float(mean_absolute_error(test["target"], predicted)),
        "rmse": float(math.sqrt(mean_squared_error(test["target"], predicted))),
        "baseline_mae": float(mean_absolute_error(test["target"], baseline)),
        "improvement_pct": float(100 * (mean_absolute_error(test["target"], baseline) - mean_absolute_error(test["target"], predicted)) / mean_absolute_error(test["target"], baseline)) if mean_absolute_error(test["target"], baseline) else None,
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = model_path.with_suffix(".cbm.tmp")
    model.save_model(str(temporary), format="cbm")
    os.replace(temporary, model_path)
    metadata = {
        "model_type": "CatBoostRegressor", "forecast_target": "daily referral count received by hospital", "horizon_days": HORIZON_DAYS,
        "source_fingerprint": fingerprint if fingerprint is not None else source_fingerprint(), "history_end": final_date.isoformat(),
        "test_period": {"start": test_start.isoformat(), "end": final_date.isoformat()},
        "rows": {"train": len(train), "test": len(test), "hospitals": int(frame["hospital_mo"].nunique())},
        "metrics": metrics, "features": FEATURE_COLUMNS,
        "limitations": [
            "Prototype forecasts referrals received, not occupied beds, capacity, staffing, or a live waiting list.",
            "Only supplied historical source parts are represented; missing source parts bias the forecast.",
            "The final seven observed calendar days form one chronological holdout; external validation is still required.",
        ],
    }
    write_json(metadata_path, metadata)
    return metadata


def forecast_status(report: dict | None = None) -> dict:
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        return {"available": False, "reason": "No 7-day referral-load model has been trained."}
    metadata = read_json(METADATA_PATH)
    stale = bool(report) and metadata.get("source_fingerprint") != report.get("source_fingerprint")
    return {"available": not stale, "stale": stale, "reason": "Refresh data and retrain the forecast model." if stale else "Forecast model ready."}


def forecast_next_week(hospital: str, hospital_day_path: Path | None = None) -> pd.DataFrame:
    """Recursively produce the next seven referral-volume estimates for one hospital."""
    status = forecast_status()
    if not status["available"]:
        raise FileNotFoundError(status["reason"])
    frame = _normalise(pd.read_parquet(hospital_day_path or PROCESSED_DIR / "hospital_day.parquet"))
    history = frame.loc[frame["hospital_mo"].eq(str(hospital))].copy()
    if len(history) < MIN_HISTORY_DAYS:
        raise ValueError("This hospital has fewer than 28 days of observed history.")
    model = CatBoostRegressor()
    model.load_model(str(MODEL_PATH), format="cbm")
    origin = history["date"].max()
    forecasts = []
    for horizon in range(1, HORIZON_DAYS + 1):
        features = pd.DataFrame([_features_at(history, origin, horizon)])[FEATURE_COLUMNS]
        value = max(0.0, float(model.predict(features)[0]))
        future_date = origin + pd.DateOffset(days=int(horizon))
        forecasts.append({"date": future_date, "predicted_referrals": value})
        # A recursive history lets later horizons use earlier estimates as recent lags.
        history = pd.concat([history, pd.DataFrame({"hospital_mo": [str(hospital)], "date": [future_date], "referrals": [value]})], ignore_index=True)
    return pd.DataFrame(forecasts)
