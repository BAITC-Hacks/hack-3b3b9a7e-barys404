import secrets

from fastapi import HTTPException

from backend.modules.auth import store
from backend.modules.auth.schemas import LoginRequest, PasswordRequest
from backend.modules.auth.store import Principal


def issue_csrf_token(
    address: str, binding: str, *, needs_preauth: bool
) -> tuple[str, str | None]:
    if not store.consume_attempt("csrf:" + address, limit=120, window=60):
        raise HTTPException(429, "Слишком много запросов. Повторите через минуту.")
    preauth = secrets.token_urlsafe(32) if needs_preauth else None
    if preauth:
        binding = "anonymous:" + store.digest(preauth)
    return store.issue_csrf(binding), preauth


def create_session(payload: LoginRequest, address: str, previous_token: str) -> str:
    login_key = store.digest(payload.login.strip().casefold())
    if not store.consume_attempt(
        "login-ip:" + address, limit=60
    ) or not store.consume_attempt("login-user:" + login_key):
        raise HTTPException(
            429, "Слишком много попыток входа. Повторите через 15 минут."
        )
    token = store.login_user(payload.login, payload.password, previous_token)
    if token is None:
        raise HTTPException(401, "Неверный логин или пароль.")
    return token


def change_password(user: Principal, payload: PasswordRequest) -> None:
    if not store.consume_attempt("password:" + user.id):
        raise HTTPException(429, "Слишком много попыток. Повторите через 15 минут.")
    if not store.change_password(user, payload.current_password, payload.new_password):
        raise HTTPException(400, "Текущий пароль указан неверно.")
