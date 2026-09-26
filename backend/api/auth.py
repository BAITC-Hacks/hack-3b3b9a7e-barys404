"""HTTP authentication and authorization dependencies."""
import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, ConfigDict

from backend.auth import store
from backend.auth.store import Principal

router = APIRouter(prefix="/api/auth", tags=["authentication"])
PRODUCTION = os.environ.get("MEDFLOW_ENV") == "production"
ORIGINS = set(os.environ.get("MEDFLOW_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:5173,http://localhost:5173").split(","))
if PRODUCTION and ("MEDFLOW_ORIGINS" not in os.environ or any(not origin.startswith("https://") for origin in ORIGINS)):
    raise RuntimeError("Production requires explicit HTTPS MEDFLOW_ORIGINS.")
SESSION_COOKIE = "__Host-medflow_session" if PRODUCTION else "medflow_session"
PREAUTH_COOKIE = "__Host-medflow_preauth" if PRODUCTION else "medflow_preauth"


def set_cookie(response, name, value, max_age):
    response.set_cookie(name, value, max_age=max_age, httponly=True, secure=PRODUCTION, samesite="lax", path="/")


def clear_session(response):
    response.delete_cookie(SESSION_COOKIE, path="/", secure=PRODUCTION, httponly=True, samesite="lax")


def csrf_binding(request):
    session = request.cookies.get(SESSION_COOKIE)
    if session:
        return "session:" + store.digest(session)
    return "anonymous:" + store.digest(request.cookies.get(PREAUTH_COOKIE, ""))


def check_csrf(request):
    if request.headers.get("origin") not in ORIGINS:
        raise HTTPException(403, "Источник запроса не разрешён.")
    token = request.headers.get("x-csrf-token", "")
    if not token or not store.valid_csrf(token, csrf_binding(request)):
        raise HTTPException(403, "Обновите страницу и повторите действие.")


def current_user(request: Request):
    user = store.session_user(request.cookies.get(SESSION_COOKIE, ""))
    if user is None:
        raise HTTPException(401, "Войдите в рабочий кабинет.")
    return user


def require(permission):
    def dependency(user: Principal = Depends(current_user)):
        if user.must_change_password:
            raise HTTPException(403, "Сначала смените временный пароль.")
        if permission not in user.permissions:
            raise HTTPException(403, "Этот раздел недоступен для вашей роли.")
        if user.role == "hospital_analyst" and not user.hospital_name:
            raise HTTPException(403, "Доступ к организации ещё не настроен. Обратитесь к администратору.")
        return user
    return dependency


def resolve_hospital(user: Principal, hospital_id: str | None, *, required=False):
    """Resolve an authorized ID to an exact data key, before any analytical reads."""
    if user.role == "hospital_analyst":
        if not user.hospital_id or not user.hospital_name:
            raise HTTPException(403, "Доступ к организации ещё не настроен.")
        if hospital_id is not None and hospital_id != user.hospital_id:
            raise HTTPException(404, "Стационар недоступен.")
        return user.hospital_name
    if user.role != "government_analyst":
        raise HTTPException(403, "Нет доступа к аналитике.")
    if hospital_id is None:
        if required:
            raise HTTPException(422, "Выберите стационар.")
        return None
    rows = store.organizations(hospital_id)
    if not rows:
        raise HTTPException(404, "Стационар недоступен.")
    return rows[0]["name"]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    login: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=128)


class PasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


@router.get("/csrf")
def csrf(request: Request, response: Response):
    if not store.consume_attempt("csrf:" + (request.client.host if request.client else "local"), limit=120, window=60):
        raise HTTPException(429, "Слишком много запросов. Повторите через минуту.")
    binding = csrf_binding(request)
    if not request.cookies.get(SESSION_COOKIE) and not request.cookies.get(PREAUTH_COOKIE):
        preauth = secrets.token_urlsafe(32)
        set_cookie(response, PREAUTH_COOKIE, preauth, 3600)
        binding = "anonymous:" + store.digest(preauth)
    return {"token": store.issue_csrf(binding)}


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response):
    address = request.client.host if request.client else "local"
    if not store.consume_attempt("login-ip:" + address, limit=60) or not store.consume_attempt("login-user:" + store.digest(payload.login.strip().casefold())):
        raise HTTPException(429, "Слишком много попыток входа. Повторите через 15 минут.")
    token = store.login_user(payload.login, payload.password, request.cookies.get(SESSION_COOKIE, ""))
    if token is None:
        raise HTTPException(401, "Неверный логин или пароль.")
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
def change_password(payload: PasswordRequest, response: Response, user: Principal = Depends(current_user)):
    if not store.consume_attempt("password:" + user.id):
        raise HTTPException(429, "Слишком много попыток. Повторите через 15 минут.")
    if not store.change_password(user, payload.current_password, payload.new_password):
        raise HTTPException(400, "Текущий пароль указан неверно.")
    clear_session(response)
    return {"ok": True}
