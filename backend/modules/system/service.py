import math
from datetime import date
from pathlib import Path
from typing import Callable

from backend.core.config import METADATA_PATH
from backend.core.utils import read_json
from backend.http import data
from backend.http.serialization import json_safe
from ml.load_forecast import METADATA_PATH as FORECAST_METADATA_PATH
from ml.load_forecast import forecast_status
from ml.predict import model_status


def get_model_status() -> dict:
    report = data.require_ready()
    waiting = model_status()
    flow = forecast_status(report)
    wait_meta = read_json(METADATA_PATH) if METADATA_PATH.exists() else {}
    flow_meta = (
        read_json(FORECAST_METADATA_PATH) if FORECAST_METADATA_PATH.exists() else {}
    )
    return json_safe(
        {
            "waiting": {
                "status": waiting,
                "metrics": wait_meta.get("metrics", {}),
                "test_period": wait_meta.get("test_period", {}),
                "rows": wait_meta.get("rows", {}),
            },
            "flow": {
                "status": flow,
                "metrics": flow_meta.get("metrics", {}),
                "history_end": flow_meta.get("history_end", "")[:10],
                "test_period": flow_meta.get("test_period", {}),
                "metrics_by_horizon": flow_meta.get("metrics_by_horizon", []),
            },
            "data": {
                "ready": report.get("pipeline_complete"),
                "summary": report.get("summary", {}),
                "coverage": report.get("coverage", {}),
                "created_at": report.get("created_at"),
            },
        }
    )


def get_methodology() -> dict:
    wait_meta = read_json(METADATA_PATH) if METADATA_PATH.exists() else {}
    flow_meta = (
        read_json(FORECAST_METADATA_PATH) if FORECAST_METADATA_PATH.exists() else {}
    )
    return json_safe(
        {
            "waiting_mae": wait_meta.get("metrics", {}).get("mae"),
            "flow_mae": flow_meta.get("metrics", {}).get("mae"),
        }
    )


def model_evidence(path: Path, status_reader: Callable[[], dict]) -> dict:
    metadata = {}
    try:
        metadata = _read_evidence_metadata(path)
        status = status_reader()
        _validate_evaluation(metadata)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        status = {
            "available": False,
            "stale": True,
            "reason": "Актуальные метрики модели недоступны. Обновите артефакты.",
        }

    return _evidence_response(metadata, status)


def _read_evidence_metadata(path: Path) -> dict:
    metadata = read_json(path)
    if isinstance(metadata, dict):
        return metadata

    raise ValueError("Invalid model metadata")


def _validate_evaluation(metadata: dict) -> None:
    period = metadata.get("test_period", {})
    if not isinstance(period, dict):
        raise ValueError("Invalid test period")

    first, last = (
        date.fromisoformat(str(period[key])[:10]) for key in ("start", "end")
    )
    if first > last or not metadata.get("model_version"):
        raise ValueError("Missing model version or invalid test period")

    metrics = metadata.get("metrics", {})
    for name in ("mae", "baseline_mae", "rmse"):
        _validate_metric(metrics[name])


def _validate_metric(value: float) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError("Invalid evaluation metric")


def _evidence_response(metadata: dict, status: dict) -> dict:
    period = metadata.get("test_period", {})
    version = metadata.get("model_version")
    metrics = metadata.get("metrics", {})

    return {
        "status": status,
        "model_version": str(version) if version is not None else None,
        "test_period": {key: str(period.get(key, ""))[:10] for key in ("start", "end")}
        if isinstance(period, dict)
        else {},
        "metrics": {key: metrics[key] for key in ("mae", "baseline_mae", "rmse")}
        if status["available"]
        else None,
    }
