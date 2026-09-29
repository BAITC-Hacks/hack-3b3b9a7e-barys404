import hashlib
import hmac
import json
from datetime import datetime, timezone

from fastapi import HTTPException

from backend.core.config import METADATA_PATH
from backend.http import data
from backend.http.serialization import json_safe
from backend.modules.analytics import dashboard_data as db
from backend.modules.analytics.schemas import ReferralFilters
from backend.modules.auth.dependencies import resolve_hospital
from backend.modules.auth.store import Principal
from backend.modules.briefings.pdf import build_briefing_pdf
from backend.modules.briefings.schemas import BriefingRequest, ReviewedBriefingRequest
from backend.modules.system.service import model_evidence
from ml.load_forecast import METADATA_PATH as FORECAST_METADATA_PATH
from ml.load_forecast import forecast_status
from ml.predict import model_status

REVIEW_QUESTIONS = {
    "waiting": "Почему различаются наблюдаемые сроки ожидания?",
    "flow": "Как изменились поток направлений и доступная мощность?",
    "refusals": "Каковы причины отказов и полнота регистрации?",
}


def build_snapshot(payload: BriefingRequest, user: Principal) -> tuple[dict, dict, str]:
    hospitals = _resolve_hospitals(payload, user)

    report = data.require_ready()
    filters = ReferralFilters(
        payload.start,
        payload.end,
        payload.region or None,
        payload.profile or None,
    ).as_dict()
    aggregates = _get_aggregates(hospitals, filters, payload.minimum)
    evidence = _get_model_evidence()
    metrics = _briefing_metrics(evidence)

    snapshot = json_safe(
        {
            "source_fingerprint": report.get("source_fingerprint"),
            "filters": filters,
            "group_dimension": "hospital_mo",
            "minimum_group_size": payload.minimum,
            "review_question": REVIEW_QUESTIONS[payload.question],
            "aggregates": aggregates,
        }
    )
    token = _review_token(snapshot, evidence, user)
    return snapshot, json_safe(metrics), token


def _resolve_hospitals(payload: BriefingRequest, user: Principal) -> list[str]:
    hospitals = [
        resolve_hospital(user, identifier, required=True)
        for identifier in payload.hospital_ids
    ]
    if len(set(hospitals)) == len(hospitals):
        return hospitals

    raise HTTPException(status_code=422, detail="Выберите разные стационары.")


def _get_aggregates(hospitals: list[str], filters: dict, minimum: int) -> list[dict]:
    aggregates = []
    for hospital in hospitals:
        table = db.compare_groups({**filters, "hospital_mo": hospital}, minimum=minimum)
        if table.empty:
            raise HTTPException(
                status_code=422,
                detail="В выбранном периоде не для всех стационаров достаточно направлений. Уточните выбор.",
            )
        aggregates.append(table.iloc[0].to_dict())
    return aggregates


def _get_model_evidence() -> dict:
    return {
        "waiting": model_evidence(METADATA_PATH, model_status),
        "forecast": model_evidence(FORECAST_METADATA_PATH, forecast_status),
    }


def _briefing_metrics(evidence: dict) -> dict:
    return {
        key: {
            **item["metrics"],
            "model_version": item["model_version"],
            "period": f"{item['test_period']['start']} - {item['test_period']['end']}",
        }
        for key, item in evidence.items()
        if item["metrics"]
    }


def _review_token(snapshot: dict, evidence: dict, user: Principal) -> str:
    paths = (
        data.ANALYTICAL_PATH,
        data.QUALITY_PATH,
        METADATA_PATH,
        FORECAST_METADATA_PATH,
    )
    context = {
        "snapshot": snapshot,
        "evidence": evidence,
        "user": user.id,
        "revisions": [db.file_version(path) for path in paths],
    }
    encoded = json.dumps(context, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def preview_briefing(payload: BriefingRequest, user: Principal) -> dict:
    snapshot, metrics, token = build_snapshot(payload, user)
    return {"snapshot": snapshot, "metrics": metrics, "review_token": token}


def render_reviewed_briefing(
    payload: ReviewedBriefingRequest, user: Principal
) -> bytes:
    snapshot, metrics, token = build_snapshot(payload, user)
    _ensure_reviewed(payload, token)

    reviewed_snapshot = {
        **snapshot,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "review_status": "reviewed_for_discussion",
    }
    return _render_pdf(reviewed_snapshot, metrics)


def _ensure_reviewed(payload: ReviewedBriefingRequest, token: str) -> None:
    if not payload.reviewed:
        raise HTTPException(
            status_code=422, detail="Сначала проверьте сводку и подтвердите просмотр."
        )
    if hmac.compare_digest(token, payload.review_token):
        return

    raise HTTPException(
        status_code=409,
        detail="Контекст сводки изменился. Загрузите новый просмотр и подтвердите его.",
    )


def _render_pdf(snapshot: dict, metrics: dict) -> bytes:
    try:
        return build_briefing_pdf(snapshot, metrics)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="Сводка не помещается на страницу. Уменьшите число стационаров.",
        ) from exc
