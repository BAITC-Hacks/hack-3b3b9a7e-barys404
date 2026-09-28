"""Bounded account administration; never return credential or session secrets."""
from backend.auth import store


def directory(search="", role=None, status=None, limit=50, offset=0):
    clauses, params = ["TRUE"], []
    if search.strip():
        clauses.append("strpos(lower(concat_ws(' ', u.login, u.display_name, o.name)), lower(%s)) > 0")
        params.append(search.strip())
    if role:
        clauses.append("u.role=%s")
        params.append(role)
    if status:
        clauses.append("u.active=%s")
        params.append(1 if status == "active" else 0)
    where = " AND ".join(clauses)
    with store.connection() as con:
        con.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        summary = dict(con.execute("""SELECT count(*) AS total,
            count(*) FILTER (WHERE active=1) AS active,
            count(*) FILTER (WHERE active=0) AS blocked FROM users""").fetchone())
        total = con.execute(f"""SELECT count(*) AS n FROM users u
            LEFT JOIN organizations o ON o.id=u.hospital_id WHERE {where}""", params).fetchone()["n"]
        rows = con.execute(f"""SELECT u.id, u.login, u.display_name, u.role,
            u.active=1 AS active, u.hospital_id, o.name AS hospital_name,
            COALESCE(o.active=1, FALSE) AS organization_active
            FROM users u LEFT JOIN organizations o ON o.id=u.hospital_id
            WHERE {where} ORDER BY u.login LIMIT %s OFFSET %s""", [*params, limit, offset]).fetchall()
        return {"items": [dict(row) for row in rows], "total": total, "summary": summary}


def change_access(actor_id, user_id, *, active=None, delete_login=None):
    """Serialize against CLI changes and protect the actor and last active admin."""
    with store.connection() as con:
        con.execute("SELECT pg_advisory_xact_lock(842732)")
        actor = con.execute("SELECT role,active,must_change_password FROM users WHERE id=%s", (actor_id,)).fetchone()
        if not actor or actor["role"] != "platform_admin" or not actor["active"] or actor["must_change_password"]:
            raise PermissionError("Нет доступа к управлению аккаунтами.")
        row = con.execute("SELECT id,login,role,active FROM users WHERE id=%s FOR UPDATE", (user_id,)).fetchone()
        if not row:
            raise LookupError("Аккаунт уже удалён или не найден. Обновите список.")
        deleting = delete_login is not None
        if deleting and delete_login != row["login"]:
            raise ValueError("Логин аккаунта изменился. Обновите список перед удалением.")
        if user_id == actor_id and (deleting or active is False):
            raise ValueError("Нельзя заблокировать или удалить свой аккаунт.")
        if row["role"] == "platform_admin" and row["active"] and (deleting or active is False):
            count = con.execute("SELECT count(*) AS n FROM users WHERE role='platform_admin' AND active=1").fetchone()["n"]
            if count <= 1:
                raise ValueError("Нельзя заблокировать или удалить последнего администратора.")
        if not deleting and bool(row["active"]) == active:
            return
        # Existing sessions must stop working immediately after either operation.
        con.execute("DELETE FROM sessions WHERE user_id=%s", (user_id,))
        if deleting:
            con.execute("DELETE FROM users WHERE id=%s", (user_id,))
            action = "user.delete"
        else:
            con.execute("UPDATE users SET active=%s,version=version+1 WHERE id=%s", (int(active), user_id))
            action = "user.unblock" if active else "user.block"
        store.audit(con, actor_id, action, row["login"])
