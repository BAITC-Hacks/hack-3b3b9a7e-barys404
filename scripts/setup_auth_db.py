"""Create a dedicated application database using a locally supplied admin URL."""
import os
import secrets
from urllib.parse import quote, urlsplit, urlunsplit

import psycopg
from psycopg import sql
from dotenv import load_dotenv, set_key, unset_key

from backend.core.config import ROOT


def main():
    env = ROOT / ".env"
    load_dotenv(env)
    admin_url = os.environ.get("MEDFLOW_ADMIN_DATABASE_URL")
    supplied = os.environ.get("MEDFLOW_DATABASE_URL")
    if not admin_url and supplied:
        parts = urlsplit(supplied)
        if parts.username == "postgres" and parts.path == "/medflow":
            # Bootstrap configuration supplied by the operator, before medflow exists.
            admin_url = urlunsplit(parts._replace(path="/postgres"))
            supplied = None
    if not admin_url:
        raise ValueError("Set MEDFLOW_ADMIN_DATABASE_URL in .env first.")
    if supplied:
        raise ValueError("Application URL already configured; refusing to replace it.")
    password = secrets.token_urlsafe(32)
    # SQL identifiers are fixed and password is a psycopg literal, never shell text.
    with psycopg.connect(admin_url, autocommit=True, connect_timeout=5) as con:
        if con.execute("SELECT 1 FROM pg_database WHERE datname='medflow'").fetchone() or con.execute("SELECT 1 FROM pg_roles WHERE rolname='medflow_app'").fetchone():
            raise ValueError("medflow database or medflow_app role already exists; configure its URL explicitly.")
        con.execute(sql.SQL("CREATE ROLE medflow_app LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Literal(password)))
        con.execute("CREATE DATABASE medflow OWNER medflow_app")
    parts = urlsplit(admin_url)
    host = parts.hostname or "127.0.0.1"
    if ":" in host:
        host = f"[{host}]"
    url = urlunsplit(("postgresql", f"medflow_app:{quote(password, safe='')}@{host}:{parts.port or 5432}", "/medflow", parts.query, ""))
    set_key(str(env), "MEDFLOW_DATABASE_URL", url)
    # The runtime only needs the restricted application credential.
    if os.environ.get("MEDFLOW_ADMIN_DATABASE_URL"):
        unset_key(str(env), "MEDFLOW_ADMIN_DATABASE_URL")
    print("Created medflow database and restricted medflow_app role. Application URL saved in .env; admin URL removed.")


if __name__ == "__main__":
    try:
        main()
    except (psycopg.Error, ValueError) as error:
        # Do not print a driver exception that may contain a connection string.
        print(str(error) if isinstance(error, ValueError) else "PostgreSQL setup failed. Check local admin credentials and database permissions.")
        raise SystemExit(1)
