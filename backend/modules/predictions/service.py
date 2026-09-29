import pandas as pd
from fastapi import HTTPException

from backend.core.config import PROCESSED_DIR
from backend.core.utils import read_json
from backend.http import data
from backend.http.serialization import json_safe
from backend.modules.analytics import dashboard_data as db
from backend.modules.analytics import repository
from backend.modules.analytics.repository import WAITING_FEATURES
from backend.modules.auth.dependencies import resolve_hospital
from backend.modules.auth.store import Principal
from backend.modules.predictions.schemas import WaitingRequest
from ml.explanations import explain_waiting
from ml.feature_engineering import make_features
from ml.load_forecast import METADATA_PATH as FORECAST_METADATA_PATH
from ml.load_forecast import forecast_next_week, forecast_status
from ml.predict import load_metadata, model_status
from ml.waiting_estimator import calibrated_predictions

HOSPITAL_MEDIAN_METHODS = {"hospital_median", "hospital_profile_median"}


def get_flow_forecast(hospital_id: str, user: Principal) -> dict:
    hospital = resolve_hospital(user, hospital_id, required=True)

    report = data.require_ready()
    data.ensure_hospital_exists(hospital)
    _ensure_forecast_available(report)

    forecast = _get_forecast(hospital)
    history = _get_recent_history(hospital)
    metadata = read_json(FORECAST_METADATA_PATH)

    return json_safe(
        {
            "history": history,
            "forecast": forecast,
            "total": float(forecast.predicted_referrals.sum()),
            "history_end": metadata.get("history_end", "")[:10],
            "metrics": metadata.get("metrics", {}),
            "metrics_by_horizon": metadata.get("metrics_by_horizon", []),
        }
    )


def _ensure_forecast_available(report: dict) -> None:
    if forecast_status(report)["available"]:
        return

    raise HTTPException(
        status_code=409,
        detail="Прогноз потока недоступен: данные или модель изменились.",
    )


def _get_forecast(hospital: str) -> pd.DataFrame:
    try:
        return forecast_next_week(hospital)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(
            status_code=422,
            detail="Для этого стационара недостаточно истории прогноза.",
        ) from exc


def _get_recent_history(hospital: str) -> pd.DataFrame:
    return (
        db.pressure_rows(PROCESSED_DIR / "hospital_day.parquet", hospital=hospital)
        .sort_values("date")
        .tail(28)[["date", "referrals"]]
    )


def get_wait_options(
    hospital_id: str | None,
    profile: str | None,
    user: Principal,
) -> dict:
    hospital = resolve_hospital(user, hospital_id, required=True)

    data.require_ready()
    _ensure_waiting_available()
    metadata = load_metadata()
    data.ensure_hospital_exists(hospital)

    options = metadata.get("feature_options", {})
    scoped_options = _get_scoped_options(hospital, profile, options)
    _ensure_profile_available(profile, scoped_options)
    example = db.representative_profile(hospital, options) if hospital else {}
    probe = _build_calibration_probe(
        hospital, profile, example, scoped_options, metadata
    )
    _, methods, support = calibrated_predictions(
        make_features(probe), [1.0], metadata["calibration"]
    )

    return json_safe(
        {
            "options": scoped_options,
            "example": example,
            "method": methods[0],
            "support": _scoped_support(methods[0], support[0]),
            "min_date": metadata["test_period"]["start"][:10],
            "default_date": metadata.get("test_period", {}).get("end", "")[:10],
            "mae": metadata.get("metrics", {}).get("mae"),
        }
    )


def _ensure_waiting_available() -> None:
    if model_status()["available"]:
        return

    raise HTTPException(status_code=409, detail="Модель ожидания недоступна.")


def _get_scoped_options(
    hospital: str,
    profile: str | None,
    options: dict,
) -> dict[str, list[str]]:
    scoped_options = {}
    for feature in WAITING_FEATURES:
        values = repository.waiting_feature_values(
            hospital, feature, profile, data.ANALYTICAL_PATH
        )
        available = [
            value
            for value in values
            if value in options.get(feature, []) and value != "__MISSING__"
        ]
        if not available:
            raise HTTPException(
                status_code=422,
                detail="Для выбранной больницы и профиля недостаточно данных для оценки.",
            )
        scoped_options[feature] = available
    return scoped_options


def _ensure_profile_available(profile: str | None, options: dict) -> None:
    if not profile or profile in options["bed_profile"]:
        return

    raise HTTPException(
        status_code=422,
        detail="Для этого профиля нет завершённых случаев в выбранном стационаре.",
    )


def _build_calibration_probe(
    hospital: str,
    profile: str | None,
    example: dict,
    options: dict,
    metadata: dict,
) -> dict:
    selected_profile = (
        profile or example.get("bed_profile") or next(iter(options["bed_profile"]), "")
    )
    probe = {
        feature: example.get(feature) or next(iter(values), "")
        for feature, values in options.items()
    }
    probe.update(
        hospital_mo=hospital,
        bed_profile=selected_profile,
        registration_dt=metadata["test_period"]["end"][:10],
    )
    return probe


def predict_wait(payload: WaitingRequest, user: Principal) -> dict:
    hospital = resolve_hospital(user, payload.hospital_id, required=True)

    data.require_ready()
    _ensure_waiting_available()
    record = _build_waiting_record(payload, hospital)
    metadata = load_metadata()
    data.ensure_hospital_exists(hospital)
    _validate_waiting_record(record, metadata)

    result = explain_waiting(record)
    return json_safe(_waiting_response(result, record, metadata))


def _build_waiting_record(payload: WaitingRequest, hospital: str) -> dict:
    record = payload.model_dump(mode="json")
    record.pop("hospital_id")
    record["hospital_mo"] = hospital
    return record


def _validate_waiting_record(record: dict, metadata: dict) -> None:
    options = metadata.get("feature_options", {})
    for feature in WAITING_FEATURES:
        if record[feature] not in options.get(feature, []):
            raise HTTPException(
                status_code=422, detail=f"Неизвестное значение поля {feature}."
            )

    first = metadata["test_period"]["start"][:10]
    last = metadata["test_period"]["end"][:10]
    if first <= record["registration_dt"] <= last:
        return

    raise HTTPException(
        status_code=422,
        detail="Дата должна находиться в периоде исторической проверки модели.",
    )


def _scoped_support(method: str, support: int) -> int:
    return support if method in HOSPITAL_MEDIAN_METHODS else 0


def _group_quality(record: dict, metadata: dict) -> dict | None:
    return next(
        (
            row
            for row in metadata.get("group_metrics", [])
            if row["hospital_mo"] == record["hospital_mo"]
            and row["bed_profile"] == record["bed_profile"]
        ),
        None,
    )


def _waiting_response(result: dict, record: dict, metadata: dict) -> dict:
    method = result.get("method", "catboost")
    support = _scoped_support(method, result.get("support", 0))
    negative = result["raw_prediction"] < 0

    return {
        "prediction": None if negative else result["prediction"],
        "raw_prediction": result["raw_prediction"],
        "clipped": negative,
        "reference": {
            "eligible": support,
            "median_wait_days": result["prediction"] if method != "catboost" else None,
        },
        "method": method,
        "support": support,
        "training_cutoff": result.get("training_cutoff", ""),
        "group_quality": _group_quality(record, metadata),
        "contributions": result["contributions"][:8],
        "mae": metadata.get("metrics", {}).get("mae"),
        "tested_until": metadata.get("test_period", {}).get("end", "")[:10],
    }
