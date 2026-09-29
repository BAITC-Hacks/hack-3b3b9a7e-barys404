from fastapi import HTTPException

from backend.modules.accounts import repository as accounts
from backend.modules.auth.store import Principal


def change_access(
    user: Principal,
    user_id: str,
    *,
    active: bool | None = None,
    delete_login: str | None = None,
) -> dict:
    try:
        accounts.change_access(
            user.id, user_id, active=active, delete_login=delete_login
        )
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    return {"ok": True}
