from fastapi import APIRouter, Depends, Query

from backend.modules.analytics import service
from backend.modules.analytics.dependencies import referral_filters
from backend.modules.analytics.schemas import ComparisonGroup, ReferralFilters
from backend.modules.auth.dependencies import require
from backend.modules.auth.store import Principal

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/bootstrap")
def bootstrap(user: Principal = Depends(require("overview:read"))):
    return service.get_bootstrap(user)


@router.get("/overview")
def overview(
    hospital_id: str | None = None,
    query: ReferralFilters = Depends(referral_filters),
    user: Principal = Depends(require("overview:read")),
):
    return service.get_overview(query, user, hospital_id)


@router.get("/compare")
def compare(
    group: ComparisonGroup = "hospital_mo",
    minimum: int = Query(30, ge=10, le=1000),
    selected: str = "",
    search: str = "",
    query: ReferralFilters = Depends(referral_filters),
    user: Principal = Depends(require("comparison:read")),
):
    return service.compare_hospitals(query, group, minimum, selected, search)
