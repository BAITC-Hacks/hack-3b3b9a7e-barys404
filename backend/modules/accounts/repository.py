from backend.modules.auth import store


def directory(search="", role=None, status=None, limit=50, offset=0):
    where, parameters = _directory_filters(search, role, status)

    with store.connection() as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        summary = _account_summary(connection)
        total = _matching_account_count(connection, where, parameters)
        rows = _account_page(connection, where, parameters, limit, offset)

    return {"items": [dict(row) for row in rows], "total": total, "summary": summary}


def _directory_filters(search, role, status) -> tuple[str, list]:
    clauses, parameters = ["TRUE"], []
    if search.strip():
        clauses.append(
            "strpos(lower(concat_ws(' ', u.login, u.display_name, o.name)), lower(%s)) > 0"
        )
        parameters.append(search.strip())
    if role:
        clauses.append("u.role=%s")
        parameters.append(role)
    if status:
        clauses.append("u.active=%s")
        parameters.append(1 if status == "active" else 0)
    return " AND ".join(clauses), parameters


def _account_summary(connection) -> dict:
    return dict(
        connection.execute("""
        SELECT count(*) AS total,
               count(*) FILTER (WHERE active=1) AS active,
               count(*) FILTER (WHERE active=0) AS blocked
        FROM users
    """).fetchone()
    )


def _matching_account_count(connection, where, parameters) -> int:
    return connection.execute(
        f"""
        SELECT count(*) AS n FROM users u
        LEFT JOIN organizations o ON o.id=u.hospital_id WHERE {where}
    """,
        parameters,
    ).fetchone()["n"]


def _account_page(connection, where, parameters, limit, offset):
    return connection.execute(
        f"""
        SELECT u.id, u.login, u.display_name, u.role,
               u.active=1 AS active, u.hospital_id, o.name AS hospital_name,
               COALESCE(o.active=1, FALSE) AS organization_active
        FROM users u LEFT JOIN organizations o ON o.id=u.hospital_id
        WHERE {where} ORDER BY u.login LIMIT %s OFFSET %s
    """,
        [*parameters, limit, offset],
    ).fetchall()


def change_access(actor_id, user_id, *, active=None, delete_login=None):
    with store.connection() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(842732)")
        _ensure_account_manager(connection, actor_id)
        account = _locked_account(connection, user_id)
        deleting = delete_login is not None
        _validate_account_change(connection, actor_id, account, active, delete_login)

        if not deleting and bool(account["active"]) == active:
            return

        _persist_account_change(connection, account, active, deleting)
        action = (
            "user.delete" if deleting else "user.unblock" if active else "user.block"
        )
        store.audit(connection, actor_id, action, account["login"])


def _ensure_account_manager(connection, actor_id) -> None:
    actor = connection.execute(
        "SELECT role,active,must_change_password FROM users WHERE id=%s",
        (actor_id,),
    ).fetchone()
    if (
        actor
        and actor["role"] == "platform_admin"
        and actor["active"]
        and not actor["must_change_password"]
    ):
        return

    raise PermissionError("Нет доступа к управлению аккаунтами.")


def _locked_account(connection, user_id):
    account = connection.execute(
        "SELECT id,login,role,active FROM users WHERE id=%s FOR UPDATE",
        (user_id,),
    ).fetchone()
    if account:
        return account

    raise LookupError("Аккаунт уже удалён или не найден. Обновите список.")


def _validate_account_change(
    connection, actor_id, account, active, delete_login
) -> None:
    deleting = delete_login is not None
    if deleting and delete_login != account["login"]:
        raise ValueError("Логин аккаунта изменился. Обновите список перед удалением.")
    if account["id"] == actor_id and (deleting or active is False):
        raise ValueError("Нельзя заблокировать или удалить свой аккаунт.")
    if (
        account["role"] != "platform_admin"
        or not account["active"]
        or not (deleting or active is False)
    ):
        return

    count = connection.execute(
        "SELECT count(*) AS n FROM users WHERE role='platform_admin' AND active=1"
    ).fetchone()["n"]
    if count <= 1:
        raise ValueError("Нельзя заблокировать или удалить последнего администратора.")


def _persist_account_change(connection, account, active, deleting) -> None:
    connection.execute("DELETE FROM sessions WHERE user_id=%s", (account["id"],))
    if deleting:
        connection.execute("DELETE FROM users WHERE id=%s", (account["id"],))
        return

    connection.execute(
        "UPDATE users SET active=%s,version=version+1 WHERE id=%s",
        (int(active), account["id"]),
    )
