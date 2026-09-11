"""Load persisted artifacts and predict with the same registration-time features."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from catboost import CatBoostRegressor
import numpy as np
import pandas as pd

from src import config
from src.data_loader import source_fingerprint
from src.feature_engineering import make_features
from src.utils import read_json


def load_metadata() -> dict:
    if not config.METADATA_PATH.exists():
        raise FileNotFoundError("Model metadata is missing. Run python -m src.train_waiting_model.")
    return read_json(config.METADATA_PATH)


def model_status() -> dict:
    if not config.MODEL_PATH.exists() or not config.METADATA_PATH.exists():
        return {"available": False, "stale": False, "reason": "Model has not been trained. Run python -m src.train_waiting_model."}
    if not config.QUALITY_PATH.exists():
        return {"available": False, "stale": True, "reason": "Data-quality report is missing; rebuild data and train the model."}
    metadata = load_metadata()
    report = read_json(config.QUALITY_PATH)
    if not report.get("pipeline_complete"):
        return {"available": False, "stale": True, "reason": "Data processing is incomplete. Finish preprocessing and retrain the model."}
    fingerprint = metadata.get("source_fingerprint")
    stale = not fingerprint or fingerprint != report.get("source_fingerprint") or fingerprint != source_fingerprint()
    return {"available": not stale, "stale": stale, "reason": "Source or processed data changed. Retrain the model." if stale else "Model ready."}


@lru_cache(maxsize=2)
def _load_model_version(path: str, modified_ns: int, file_size: int) -> CatBoostRegressor:
    model = CatBoostRegressor()
    model.load_model(path, format="cbm")
    return model


def load_model() -> CatBoostRegressor:
    status = model_status()
    if not status["available"]:
        raise FileNotFoundError(status["reason"])
    model_path = Path(config.MODEL_PATH)
    stat = model_path.stat()
    return _load_model_version(str(model_path), stat.st_mtime_ns, stat.st_size)


def predict_waiting_time(record: dict) -> float:
    """Return typical wait in days for one referral, with no generated fallback."""
    features = make_features(record)
    value = float(load_model().predict(features)[0])
    if not np.isfinite(value):
        raise ValueError("The model returned a non-finite estimate.")
    return max(0.0, value)


def predict_batch(records: pd.DataFrame) -> np.ndarray:
    """Reusable inference boundary for a future API (not a patient-level UI)."""
    predictions = np.asarray(load_model().predict(make_features(records)), dtype=float)
    if not np.isfinite(predictions).all():
        raise ValueError("The model returned non-finite estimates.")
    return np.maximum(0.0, predictions)
