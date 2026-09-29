from fastapi import HTTPException

from backend.core.config import ANALYTICAL_PATH, QUALITY_PATH
from backend.core.utils import read_json
from backend.data_pipeline.data_loader import source_fingerprint
from backend.modules.analytics import repository


def require_ready() -> dict:
    if not ANALYTICAL_PATH.exists() or not QUALITY_PATH.exists():
        raise HTTPException(
            503, "Подготовленные данные не найдены. Запустите подготовку данных."
        )
    report = read_json(QUALITY_PATH)
    if not report.get("pipeline_complete"):
        raise HTTPException(503, "Подготовка данных не завершена.")
    if report.get("source_fingerprint") != source_fingerprint():
        raise HTTPException(
            409,
            "Исходные CSV изменились. Обновите данные и модели через python -m scripts.bootstrap.",
        )
    return report


def ensure_hospital_exists(hospital: str) -> None:
    if len(hospital) > 300:
        raise HTTPException(422, "Название стационара слишком длинное.")
    if not repository.hospital_exists(hospital, ANALYTICAL_PATH):
        raise HTTPException(404, "Стационар недоступен.")
