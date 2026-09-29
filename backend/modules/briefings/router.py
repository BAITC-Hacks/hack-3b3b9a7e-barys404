from fastapi import APIRouter, Depends, Response

from backend.modules.auth.dependencies import require
from backend.modules.auth.store import Principal
from backend.modules.briefings import service
from backend.modules.briefings.schemas import BriefingRequest, ReviewedBriefingRequest

router = APIRouter(prefix="/api/briefings", tags=["briefings"])


@router.post("/preview")
def briefing_preview(
    payload: BriefingRequest,
    user: Principal = Depends(require("briefing:export")),
):
    return service.preview_briefing(payload, user)


@router.post("/pdf")
def briefing_pdf(
    payload: ReviewedBriefingRequest,
    user: Principal = Depends(require("briefing:export")),
):
    pdf = service.render_reviewed_briefing(payload, user)
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="medflow_briefing.pdf"'},
    )
