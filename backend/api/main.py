"""Local, aggregate-only API for the MedFlow web dashboard."""
from __future__ import annotations

from datetime import date
from functools import lru_cache
import math
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import numpy as np
import pandas as pd

from backend.analytics import dashboard_data as db
from backend.core.config import ANALYTICAL_PATH, METADATA_PATH, PROCESSED_DIR, QUALITY_PATH, ROOT
from backend.data_pipeline.data_loader import source_fingerprint
from ml.explanations import explain_waiting
from ml.load_forecast import (
    METADATA_PATH as FORECAST_METADATA_PATH,
    forecast_next_week,
    forecast_status,
)
from ml.predict import load_metadata, model_status
from ml.feature_engineering import make_features
from ml.waiting_estimator import calibrated_predictions
from backend.core.utils import read_json


app = FastAPI(title="MedFlow AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def clean(value):
    """Make bounded pandas aggregates safe for JSON without exposing row data."""
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, pd.DataFrame):
        return [clean(row) for row in value.to_dict(orient="records")]
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, (pd.Timestamp, date)):
        return value.isoformat()[:10]
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def ready():
    if not ANALYTICAL_PATH.exists() or not QUALITY_PATH.exists():
        raise HTTPException(503, "Подготовленные данные не найдены. Запустите подготовку данных.")
    report = read_json(QUALITY_PATH)
    if not report.get("pipeline_complete"):
        raise HTTPException(503, "Подготовка данных не завершена.")
    if report.get("source_fingerprint") != source_fingerprint():
        raise HTTPException(409, "Исходные CSV изменились. Обновите данные и модели через python -m scripts.bootstrap.")
    return report


def filters_from(start: date | None, end: date | None, region: str | None,
                 profile: str | None, hospital: str | None = None):
    if start and end and start > end:
        raise HTTPException(422, "Начало периода должно быть раньше конца.")
    filters = {"start": start, "end": end,
               "region_origin_code": region, "bed_profile": profile,
               "hospital_mo": hospital}
    return {key: value for key, value in filters.items() if value is not None}


def check_hospital(hospital: str):
    if len(hospital) > 300:
        raise HTTPException(422, "Название стационара слишком длинное.")
    result = db.aggregate_query(
        ANALYTICAL_PATH,
        "SELECT count(*) AS n FROM read_parquet(?) WHERE hospital_mo = ?",
        [hospital],
    )
    if not result.iloc[0]["n"]:
        raise HTTPException(404, "Стационар не найден в подготовленных данных.")


@lru_cache(maxsize=4)
def cached_dimensions(version):
    return db.dimensions()


@app.get("/api/health")
def health():
    report = ready()
    return clean({"ready": True, "period": report.get("summary", {}),
                  "waiting_model": model_status(),
                  "flow_model": forecast_status(report)})


@app.get("/api/bootstrap")
def bootstrap():
    report = ready()
    dimensions = cached_dimensions(db.file_version(ANALYTICAL_PATH))
    summary = report.get("summary", {})
    featured_rows = db.aggregate_query(ANALYTICAL_PATH, """
        SELECT hospital_mo FROM read_parquet(?) WHERE hospital_mo IS NOT NULL
        GROUP BY 1 ORDER BY count(*) DESC, hospital_mo LIMIT 1
    """)
    featured = str(featured_rows.iloc[0]["hospital_mo"]) if not featured_rows.empty else ""
    return clean({
        "period": {"start": str(dimensions["dates"]["first"])[:10],
                   "end": str(dimensions["dates"]["last"])[:10]},
        "regions": dimensions["region_origin_code"],
        "profiles": [value for value in dimensions["bed_profile"] if value != "__MISSING__"],
        "hospitals": dimensions["hospital_mo"],
        "featured_hospital": featured,
        "summary": {key: summary.get(key) for key in (
            "referral_records", "hospitals", "regions", "target_eligible")},
    })


@app.get("/api/overview")
def overview(start: date | None = None, end: date | None = None,
             region: str | None = None, profile: str | None = None,
             hospital: str | None = None):
    ready()
    filters = filters_from(start, end, region, profile, hospital)
    stats = db.overview(filters)
    where, params = db.cohort_where(filters)
    trend = db.aggregate_query(ANALYTICAL_PATH, f"""
        SELECT CAST(date_trunc('week', registration_dt) AS DATE) AS week,
               count(*) AS referrals
        FROM read_parquet(?) WHERE {where}
        GROUP BY 1 ORDER BY 1
    """, params)
    period, changes = db.recent_activity(filters)
    if hospital:
        changes = changes.loc[changes.hospital.eq(hospital)]
    changes = changes.loc[
        (changes.previous >= 10) & (changes.current >= 10) & (changes.change_pct > 0)
    ].sort_values("change_pct", ascending=False).head(4)
    return clean({"stats": stats, "trend": trend, "attention_period": period,
                  "attention": changes})


@app.get("/api/hospitals")
def hospitals(start: date | None = None, end: date | None = None,
              region: str | None = None, profile: str | None = None,
              search: str = "", limit: int = Query(50, ge=1, le=100),
              offset: int = Query(0, ge=0)):
    ready()
    filters = filters_from(start, end, region, profile)
    table = db.hospital_directory(filters)
    if search:
        table = table.loc[table.organization_or_region.str.contains(search[:100], case=False, regex=False)]
    return clean({"total": len(table), "items": table.iloc[offset:offset + limit]})


@app.get("/api/hospital/overview")
def hospital_overview(hospital: str, start: date | None = None, end: date | None = None,
                      region: str | None = None, profile: str | None = None):
    ready()
    check_hospital(hospital)
    filters = filters_from(start, end, region, profile, hospital)
    comparison = db.hospital_directory(filters)
    row = comparison.iloc[0].to_dict() if not comparison.empty else None
    profiles = db.hospital_profiles(filters)
    return clean({"hospital": hospital, "stats": row, "profiles": profiles})


@app.get("/api/hospital/forecast")
def hospital_forecast(hospital: str):
    report = ready()
    check_hospital(hospital)
    status = forecast_status(report)
    if not status["available"]:
        raise HTTPException(409, "Прогноз потока недоступен: данные или модель изменились.")
    try:
        future = forecast_next_week(hospital)
    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(422, "Для этого стационара недостаточно истории прогноза.") from error
    history = db.pressure_rows(PROCESSED_DIR / "hospital_day.parquet", hospital=hospital)
    history = history.sort_values("date").tail(28)[["date", "referrals"]]
    metadata = read_json(FORECAST_METADATA_PATH)
    return clean({"history": history, "forecast": future,
                  "total": float(future.predicted_referrals.sum()),
                  "history_end": metadata.get("history_end", "")[:10],
                  "metrics": metadata.get("metrics", {}),
                  "metrics_by_horizon": metadata.get("metrics_by_horizon", [])})


@app.get("/api/compare")
def compare(start: date | None = None, end: date | None = None,
            region: str | None = None, profile: str | None = None,
            group: Literal["hospital_mo", "region_origin_code"] = "hospital_mo",
            minimum: int = Query(30, ge=10, le=1000),
            selected: str = "", search: str = ""):
    ready()
    filters = filters_from(start, end, region, profile)
    table = db.compare_groups(filters, group_by=group, minimum=minimum)
    names = [name for name in selected.split("|") if name][:3]
    if search:
        mask = table.organization_or_region.str.contains(search[:100], case=False, regex=False)
        table = table.loc[mask | table.organization_or_region.isin(names)]
    if names:
        chosen = table.loc[table.organization_or_region.isin(names)]
        others = table.loc[~table.organization_or_region.isin(names)]
        table = pd.concat([chosen, others], ignore_index=True)
    return clean({"items": table.head(50), "total": len(table)})


@app.get("/api/models")
def models():
    report = ready()
    waiting = model_status()
    flow = forecast_status(report)
    wait_meta = read_json(METADATA_PATH) if METADATA_PATH.exists() else {}
    flow_meta = read_json(FORECAST_METADATA_PATH) if FORECAST_METADATA_PATH.exists() else {}
    return clean({
        "waiting": {"status": waiting, "metrics": wait_meta.get("metrics", {}),
                    "test_period": wait_meta.get("test_period", {}),
                    "rows": wait_meta.get("rows", {})},
        "flow": {"status": flow, "metrics": flow_meta.get("metrics", {}),
                 "history_end": flow_meta.get("history_end", "")[:10],
                 "test_period": flow_meta.get("test_period", {}),
                 "metrics_by_horizon": flow_meta.get("metrics_by_horizon", [])},
        "data": {"ready": report.get("pipeline_complete"),
                 "summary": report.get("summary", {}),
                 "coverage": report.get("coverage", {}),
                 "created_at": report.get("created_at")},
    })


@app.get("/api/wait-options")
def wait_options(hospital: str | None = None, profile: str | None = None):
    ready()
    if not model_status()["available"]:
        raise HTTPException(409, "Модель ожидания недоступна.")
    metadata = load_metadata()
    options = metadata.get("feature_options", {})
    if hospital:
        check_hospital(hospital)
    else:
        hospital = next(iter(options.get("hospital_mo", [])), None)
    scoped_options = {}
    for key in ("icd10_ref_diag_code", "bed_profile", "territorial_type",
                "referral_purpose", "finance_source"):
        where_profile = "AND bed_profile = ?" if profile and key != "bed_profile" else ""
        values = db.aggregate_query(ANALYTICAL_PATH, f"""
            SELECT DISTINCT {key} AS value FROM read_parquet(?)
            WHERE hospital_mo = ? {where_profile}
              AND {key} IS NOT NULL ORDER BY value
        """, [hospital, *([profile] if where_profile else [])])["value"].astype(str).tolist()
        scoped_options[key] = [value for value in values if value in options.get(key, []) and value != "__MISSING__"]
        if not scoped_options[key]:
            scoped_options[key] = [value for value in options.get(key, []) if value != "__MISSING__"]
    if profile and profile not in scoped_options["bed_profile"]:
        raise HTTPException(422, "Для этого профиля нет завершённых случаев в выбранном стационаре.")
    example = {}
    if hospital:
        example = db.representative_profile(hospital, options)
    selected_profile = profile or example.get("bed_profile") or next(iter(scoped_options["bed_profile"]), "")
    probe = {key: example.get(key) or next(iter(values), "") for key, values in scoped_options.items()}
    probe.update(hospital_mo=hospital, bed_profile=selected_profile, registration_dt=metadata["test_period"]["end"][:10])
    _, methods, support = calibrated_predictions(make_features(probe), [1.], metadata["calibration"])
    return clean({"options": scoped_options,
                  "example": example,
                  "method": methods[0], "support": support[0],
                  "min_date": metadata["test_period"]["start"][:10],
                  "default_date": metadata.get("test_period", {}).get("end", "")[:10],
                  "mae": metadata.get("metrics", {}).get("mae")})


class WaitingRequest(BaseModel):
    hospital_mo: str = Field(min_length=1)
    icd10_ref_diag_code: str = Field(min_length=1)
    bed_profile: str = Field(min_length=1)
    territorial_type: str = Field(min_length=1)
    referral_purpose: str = Field(min_length=1)
    finance_source: str = Field(min_length=1)
    registration_dt: date


@app.post("/api/predictions/wait")
def predict_wait(payload: WaitingRequest):
    ready()
    if not model_status()["available"]:
        raise HTTPException(409, "Модель ожидания недоступна.")
    record = payload.model_dump(mode="json")
    metadata = load_metadata()
    options = metadata.get("feature_options", {})
    check_hospital(record["hospital_mo"])
    for key in ("icd10_ref_diag_code", "bed_profile", "territorial_type",
                "referral_purpose", "finance_source"):
        if record[key] not in options.get(key, []):
            raise HTTPException(422, f"Неизвестное значение поля {key}.")
    if not metadata["test_period"]["start"][:10] <= record["registration_dt"] <= metadata["test_period"]["end"][:10]:
        raise HTTPException(422, "Дата должна находиться в периоде исторической проверки модели.")
    result = explain_waiting(record)
    method = result.get("method", "catboost")
    reference = {"eligible": result.get("support", 0),
                 "median_wait_days": result["prediction"] if method != "catboost" else None}
    group_quality = next((row for row in metadata.get("group_metrics", [])
                          if row["hospital_mo"] == record["hospital_mo"]
                          and row["bed_profile"] == record["bed_profile"]), None)
    return clean({"prediction": None if result["raw_prediction"] < 0 else result["prediction"],
                  "raw_prediction": result["raw_prediction"],
                  "clipped": result["raw_prediction"] < 0,
                  "reference": reference,
                  "method": method, "support": result.get("support", 0),
                  "training_cutoff": result.get("training_cutoff", ""),
                  "group_quality": group_quality,
                  "contributions": result["contributions"][:8],
                  "mae": metadata.get("metrics", {}).get("mae"),
                  "tested_until": metadata.get("test_period", {}).get("end", "")[:10]})


# A built frontend is served by the same local process for an offline demo.
DIST = ROOT / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/favicon.svg", include_in_schema=False)
    def favicon():
        return FileResponse(DIST / "favicon.svg", media_type="image/svg+xml")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        return FileResponse(DIST / "index.html")
