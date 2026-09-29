from fastapi import APIRouter, Depends, Request, Response

from backend.modules.auth import service, store
from backend.modules.auth.config import PREAUTH_COOKIE, PRODUCTION, SESSION_COOKIE
from backend.modules.auth.dependencies import csrf_binding, current_user
from backend.modules.auth.schemas import LoginRequest, PasswordRequest
from backend.modules.auth.store import Principal

router = APIRouter(prefix="/api/auth", tags=["authentication"])


def set_cookie(response: Response, name: str, value: str, max_age: int) -> None:
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        httponly=True,
        secure=PRODUCTION,
        samesite="lax",
        path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        secure=PRODUCTION,
        httponly=True,
        samesite="lax",
    )


@router.get("/csrf")
def csrf(request: Request, response: Response):
    token, preauth = service.issue_csrf_token(
        request.client.host if request.client else "local",
        csrf_binding(request),
        needs_preauth=not request.cookies.get(SESSION_COOKIE)
        and not request.cookies.get(PREAUTH_COOKIE),
    )
    if preauth:
        set_cookie(response, PREAUTH_COOKIE, preauth, 3600)
    return {"token": token}


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response):
    token = service.create_session(
        payload,
        request.client.host if request.client else "local",
        request.cookies.get(SESSION_COOKIE, ""),
    )
    set_cookie(response, SESSION_COOKIE, token, 28800)
    return store.session_user(token).public()


@router.get("/me")
def me(user: Principal = Depends(current_user)):
    return user.public()


@router.post("/activity")
def activity(request: Request, user: Principal = Depends(current_user)):
    store.session_user(request.cookies.get(SESSION_COOKIE, ""), touch=True)
    return {"ok": True}


@router.post("/logout")
def logout(request: Request, response: Response):
    store.logout(request.cookies.get(SESSION_COOKIE, ""))
    clear_session(response)
    return {"ok": True}


@router.post("/change-password")
def change_password(
    payload: PasswordRequest,
    response: Response,
    user: Principal = Depends(current_user),
):
    service.change_password(user, payload)
    clear_session(response)
    return {"ok": True}
