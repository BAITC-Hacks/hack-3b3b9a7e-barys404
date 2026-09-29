from fastapi import APIRouter, Depends, Query

from backend.modules.analytics.dependencies import referral_filters
from backend.modules.analytics.schemas import ReferralFilters
from backend.modules.auth.dependencies import require
from backend.modules.auth.store import Principal
from backend.modules.hospitals import service

router = APIRouter(prefix="/api", tags=["hospitals"])


@router.get("/hospitals")
def hospitals(
    search: str = "",
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    query: ReferralFilters = Depends(referral_filters),
    user: Principal = Depends(require("hospital:list")),
):
    return service.list_hospitals(query, search, limit, offset)


@router.get("/hospital/overview")
def hospital_overview(
    hospital_id: str,
    query: ReferralFilters = Depends(referral_filters),
    user: Principal = Depends(require("hospital:read")),
):
    return service.get_hospital_overview(hospital_id, user, query)
