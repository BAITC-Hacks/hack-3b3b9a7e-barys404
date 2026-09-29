from fastapi import APIRouter, Depends

from backend.modules.auth.dependencies import require
from backend.modules.auth.store import Principal
from backend.modules.predictions import service
from backend.modules.predictions.schemas import WaitingRequest

router = APIRouter(prefix="/api", tags=["predictions"])


@router.get("/hospital/forecast")
def hospital_forecast(
    hospital_id: str,
    user: Principal = Depends(require("forecast:read")),
):
    return service.get_flow_forecast(hospital_id, user)


@router.get("/wait-options")
def wait_options(
    hospital_id: str | None = None,
    profile: str | None = None,
    user: Principal = Depends(require("waiting:predict")),
):
    return service.get_wait_options(hospital_id, profile, user)


@router.post("/predictions/wait")
def predict_wait(
    payload: WaitingRequest,
    user: Principal = Depends(require("waiting:predict")),
):
    return service.predict_wait(payload, user)
