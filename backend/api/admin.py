"""Admin-only account list and explicit, CSRF-protected access changes."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from backend.api.auth import require
from backend.auth import accounts
from backend.auth.store import Principal

router = APIRouter(prefix="/api/admin", tags=["administration"])


@router.get("/users")
def users(search: str = Query("", max_length=120),
          role: Literal["government_analyst", "hospital_analyst", "platform_admin"] | None = None,
          status: Literal["active", "blocked"] | None = None,
          limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=1000000),
          user: Principal = Depends(require("system:read"))):
    return accounts.directory(search, role, status, limit, offset)


class AccessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    active: StrictBool


class DeleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    login: str = Field(min_length=1, max_length=120)


def apply_change(user, user_id, **values):
    try:
        accounts.change_access(user.id, user_id, **values)
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    return {"ok": True}


@router.post("/users/{user_id}/status")
def status(user_id: str, payload: AccessRequest, user: Principal = Depends(require("accounts:manage"))):
    return apply_change(user, user_id, active=payload.active)


@router.post("/users/{user_id}/delete")
def delete(user_id: str, payload: DeleteRequest, user: Principal = Depends(require("accounts:manage"))):
    return apply_change(user, user_id, delete_login=payload.login)
