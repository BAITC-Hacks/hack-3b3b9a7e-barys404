"""PostgreSQL authentication store. No default users or passwords."""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import secrets
import re
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
import time
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError

from backend.core.config import ROOT

HASHER = PasswordHasher()
# Equal-cost password verification when the login does not exist.
DUMMY_HASH = HASHER.hash(secrets.token_urlsafe(32))
ANALYST = frozenset({"overview:read", "hospital:read", "forecast:read", "waiting:predict", "methodology:read"})
PERMISSIONS = {
    "government_analyst": ANALYST | {"hospital:list", "comparison:read"},
    "hospital_analyst": ANALYST,
    "platform_admin": frozenset({"system:read", "methodology:read"}),
}


load_dotenv(ROOT / ".env")


def database_url():
    value = os.environ.get("MEDFLOW_DATABASE_URL")
    if not value:
        raise RuntimeError("Настройте MEDFLOW_DATABASE_URL и выполните python -m scripts.auth migrate.")
    return value


def schema_name():
    name = os.environ.get("MEDFLOW_AUTH_SCHEMA", "public")
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", name):
        raise ValueError("Invalid database schema")
    return name


@contextmanager
def connection():
    with psycopg.connect(database_url(), row_factory=dict_row, connect_timeout=5,
                         options=f"-c search_path={schema_name()}") as con:
        yield con


def migrate():
    with connection() as con:
        con.execute("SELECT pg_advisory_xact_lock(842731)")
        con.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)")
        if not con.execute("SELECT 1 FROM schema_migrations WHERE version=1").fetchone():
            con.execute((Path(__file__).parent / "migrations" / "001_accounts.sql").read_text(encoding="utf-8"))
            con.execute("INSERT INTO schema_migrations VALUES(1)")


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def audit(con, actor, action, target="", result="ok"):
    con.execute("INSERT INTO audit_events(at,actor,action,target,result) VALUES(%s,%s,%s,%s,%s)",
                (time.time(), actor, action, target, result))


@dataclass(frozen=True)
class Principal:
    id: str
    login: str
    display_name: str
    role: str
    hospital_id: str | None
    hospital_name: str | None
    must_change_password: bool = False

    @property
    def permissions(self):
        return PERMISSIONS.get(self.role, frozenset())

    def public(self):
        return {"id": self.id, "login": self.login, "display_name": self.display_name,
                "role": self.role, "permissions": sorted(self.permissions),
                "hospital_id": self.hospital_id, "hospital_name": self.hospital_name,
                "must_change_password": self.must_change_password}


def principal(row):
    return Principal(row["id"], row["login"], row["display_name"], row["role"],
                     row["hospital_id"], row["hospital_name"], bool(row["must_change_password"]))


def validate_password(password):
    if not 12 <= len(password) <= 128:
        raise ValueError("Пароль должен содержать от 12 до 128 символов.")


def verify(password_hash, password):
    try:
        return HASHER.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def sync_organizations(names):
    """Explicit catalog sync: exact names only; never reassign accounts by similarity."""
    names = sorted(set(names))
    with connection() as con:
        con.execute("UPDATE organizations SET active=0")
        for name in names:
            con.execute("INSERT INTO organizations(id,name,active) VALUES(%s,%s,1) "
                        "ON CONFLICT(name) DO UPDATE SET active=1", (str(uuid.uuid4()), name))
        con.execute("DELETE FROM sessions WHERE user_id IN (SELECT u.id FROM users u JOIN organizations o ON o.id=u.hospital_id WHERE o.active=0)")
        audit(con, "operator", "organizations.sync")


def organizations(hospital_id=None):
    with connection() as con:
        sql = "SELECT id,name FROM organizations WHERE active=1"
        rows = con.execute(sql + (" AND id=%s" if hospital_id else "") + " ORDER BY name",
                           (hospital_id,) if hospital_id else ()).fetchall()
        return [dict(row) for row in rows]


def create_user(login, display_name, password, role, hospital_id=None, must_change=True):
    validate_password(password)
    login = login.strip().casefold()
    if not login or len(login) > 120 or role not in PERMISSIONS:
        raise ValueError("Проверьте логин и роль.")
    if role == "hospital_analyst" and not hospital_id:
        raise ValueError("Сотруднику больницы необходимо назначить организацию.")
    if role != "hospital_analyst" and hospital_id:
        raise ValueError("Привязка к больнице используется только для сотрудника больницы.")
    hashed = HASHER.hash(password)
    with connection() as con:
        if hospital_id and not con.execute("SELECT 1 FROM organizations WHERE id=%s AND active=1", (hospital_id,)).fetchone():
            raise ValueError("Организация не найдена.")
        uid = str(uuid.uuid4())
        con.execute("INSERT INTO users(id,login,display_name,password_hash,role,hospital_id,must_change_password) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    (uid, login, display_name, hashed, role, hospital_id, int(must_change)))
        audit(con, "operator", "user.create", uid)
        return uid


def list_users():
    with connection() as con:
        return [dict(row) for row in con.execute("SELECT id,login,display_name,role,hospital_id,active FROM users ORDER BY login")]


def update_user(login, *, active=None, role=None, hospital_id=None, password=None):
    if password is not None:
        validate_password(password)
    with connection() as con:
        con.execute("SELECT pg_advisory_xact_lock(842732)")
        row = con.execute("SELECT * FROM users WHERE login=%s FOR UPDATE", (login.strip().casefold(),)).fetchone()
        if not row:
            raise ValueError("Пользователь не найден.")
        next_role = role or row["role"]
        next_active = row["active"] if active is None else int(active)
        next_hospital = (hospital_id if hospital_id is not None else row["hospital_id"]) if next_role == "hospital_analyst" else None
        if next_role not in PERMISSIONS:
            raise ValueError("Неизвестная роль.")
        if next_role == "hospital_analyst" and not con.execute("SELECT 1 FROM organizations WHERE id=%s AND active=1", (next_hospital,)).fetchone():
            raise ValueError("Назначьте действующую больницу.")
        if row["role"] == "platform_admin" and row["active"] and (not next_active or next_role != "platform_admin"):
            if con.execute("SELECT count(*) AS n FROM users WHERE role='platform_admin' AND active=1").fetchone()["n"] <= 1:
                raise ValueError("Нельзя отключить последнего администратора.")
        con.execute("UPDATE users SET active=%s,role=%s,hospital_id=%s,password_hash=%s,must_change_password=%s,version=version+1 WHERE id=%s",
                    (next_active, next_role, next_hospital, HASHER.hash(password) if password else row["password_hash"],
                     1 if password else row["must_change_password"], row["id"]))
        con.execute("DELETE FROM sessions WHERE user_id=%s", (row["id"],))
        audit(con, "operator", "user.update_and_revoke", row["id"])


def consume_attempt(bucket, limit=10, window=900):
    """Persistent, transactional limiter shared by local workers."""
    now = time.time()
    with connection() as con:
        con.execute("SELECT pg_advisory_xact_lock(%s)", (int(digest(bucket)[:15], 16),))
        con.execute("DELETE FROM attempts WHERE started<%s", (now - window,))
        row = con.execute("SELECT count FROM attempts WHERE bucket=%s", (bucket,)).fetchone()
        allowed = row is None or row["count"] < limit
        if allowed:
            con.execute("INSERT INTO attempts VALUES(%s,%s,1) ON CONFLICT(bucket) DO UPDATE SET count=attempts.count+1", (bucket, now))
        return allowed


def login_user(login, password, old_token=""):
    normalized = login.strip().casefold()
    with connection() as con:
        row = con.execute("SELECT * FROM users WHERE login=%s", (normalized,)).fetchone()
        valid = verify(row["password_hash"] if row else DUMMY_HASH, password)
        if not row or not valid or not row["active"]:
            audit(con, row["id"] if row else "anonymous", "login", result="denied")
            return None
        if HASHER.check_needs_rehash(row["password_hash"]):
            con.execute("UPDATE users SET password_hash=%s WHERE id=%s", (HASHER.hash(password), row["id"]))
        con.execute("DELETE FROM sessions WHERE token_hash=%s OR created<%s", (digest(old_token), time.time() - 28800))
        token = secrets.token_urlsafe(32)
        now = time.time()
        con.execute("INSERT INTO sessions VALUES(%s,%s,%s,%s,%s)", (digest(token), row["id"], row["version"], now, now))
        audit(con, row["id"], "login")
        return token


def session_user(token, touch=False):
    if not token:
        return None
    now = time.time()
    with connection() as con:
        row = con.execute("""SELECT u.*, o.name AS hospital_name, s.created, s.last_active,
            s.version AS session_version FROM sessions s JOIN users u ON u.id=s.user_id
            LEFT JOIN organizations o ON o.id=u.hospital_id AND o.active=1 WHERE s.token_hash=%s""", (digest(token),)).fetchone()
        if not row:
            return None
        if not row["active"] or row["version"] != row["session_version"] or now - row["created"] >= 28800 or now - row["last_active"] >= 1800:
            con.execute("DELETE FROM sessions WHERE token_hash=%s", (digest(token),))
            return None
        if touch:
            con.execute("UPDATE sessions SET last_active=%s WHERE token_hash=%s", (now, digest(token)))
        return principal(row)


def logout(token):
    with connection() as con:
        row = con.execute("SELECT user_id FROM sessions WHERE token_hash=%s", (digest(token),)).fetchone()
        con.execute("DELETE FROM sessions WHERE token_hash=%s", (digest(token),))
        if row:
            audit(con, row["user_id"], "logout")


def change_password(user, current, new):
    validate_password(new)
    with connection() as con:
        row = con.execute("SELECT password_hash FROM users WHERE id=%s FOR UPDATE", (user.id,)).fetchone()
        if not row or not verify(row["password_hash"], current):
            return False
        con.execute("UPDATE users SET password_hash=%s,must_change_password=0,version=version+1 WHERE id=%s", (HASHER.hash(new), user.id))
        con.execute("DELETE FROM sessions WHERE user_id=%s", (user.id,))
        audit(con, user.id, "password.change")
        return True


def issue_csrf(binding):
    token = secrets.token_urlsafe(32)
    with connection() as con:
        con.execute("DELETE FROM csrf_tokens WHERE expires<%s", (time.time(),))
        con.execute("INSERT INTO csrf_tokens VALUES(%s,%s,%s)", (digest(token), binding, time.time() + 3600))
    return token


def valid_csrf(token, binding):
    with connection() as con:
        return con.execute("SELECT 1 FROM csrf_tokens WHERE token_hash=%s AND binding=%s AND expires>%s",
                           (digest(token), binding, time.time())).fetchone() is not None
