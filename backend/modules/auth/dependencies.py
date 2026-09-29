from collections.abc import Callable

from fastapi import Depends, HTTPException, Request

from backend.modules.auth import store
from backend.modules.auth.config import ORIGINS, PREAUTH_COOKIE, SESSION_COOKIE
from backend.modules.auth.store import Principal


def csrf_binding(request: Request) -> str:
    session = request.cookies.get(SESSION_COOKIE)
    if session:
        return "session:" + store.digest(session)
    return "anonymous:" + store.digest(request.cookies.get(PREAUTH_COOKIE, ""))


def check_csrf(request: Request) -> None:
    if request.headers.get("origin") not in ORIGINS:
        raise HTTPException(403, "Источник запроса не разрешён.")
    token = request.headers.get("x-csrf-token", "")
    if not token or not store.valid_csrf(token, csrf_binding(request)):
        raise HTTPException(403, "Обновите страницу и повторите действие.")


def current_user(request: Request) -> Principal:
    user = store.session_user(request.cookies.get(SESSION_COOKIE, ""))
    if user is None:
        raise HTTPException(401, "Войдите в рабочий кабинет.")
    return user


def require(permission: str) -> Callable[..., Principal]:
    def dependency(user: Principal = Depends(current_user)) -> Principal:
        if user.must_change_password:
            raise HTTPException(403, "Сначала смените временный пароль.")
        if permission not in user.permissions:
            raise HTTPException(403, "Этот раздел недоступен для вашей роли.")
        if user.role == "hospital_analyst" and not user.hospital_name:
            raise HTTPException(
                403,
                "Доступ к организации ещё не настроен. Обратитесь к администратору.",
            )
        return user

    return dependency


def resolve_hospital(
    user: Principal, hospital_id: str | None, *, required: bool = False
) -> str | None:
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
