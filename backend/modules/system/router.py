from fastapi import APIRouter, Depends

from backend.modules.auth.dependencies import require
from backend.modules.auth.store import Principal
from backend.modules.system import service

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/models")
def models(user: Principal = Depends(require("system:read"))):
    return service.get_model_status()


@router.get("/methodology")
def methodology(user: Principal = Depends(require("methodology:read"))):
    return service.get_methodology()
