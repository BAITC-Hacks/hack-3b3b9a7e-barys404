from typing import Literal

from fastapi import APIRouter, Depends, Query

from backend.modules.accounts import repository as accounts
from backend.modules.accounts import service
from backend.modules.accounts.schemas import AccessRequest, DeleteRequest
from backend.modules.auth.dependencies import require
from backend.modules.auth.store import Principal

router = APIRouter(prefix="/api/admin", tags=["administration"])


@router.get("/users")
def users(
    search: str = Query("", max_length=120),
    role: Literal["government_analyst", "hospital_analyst", "platform_admin"]
    | None = None,
    status: Literal["active", "blocked"] | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0, le=1000000),
    user: Principal = Depends(require("system:read")),
):
    return accounts.directory(search, role, status, limit, offset)


@router.post("/users/{user_id}/status")
def status(
    user_id: str,
    payload: AccessRequest,
    user: Principal = Depends(require("accounts:manage")),
):
    return service.change_access(user, user_id, active=payload.active)


@router.post("/users/{user_id}/delete")
def delete(
    user_id: str,
    payload: DeleteRequest,
    user: Principal = Depends(require("accounts:manage")),
):
    return service.change_access(user, user_id, delete_login=payload.login)
