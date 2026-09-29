import os

from dotenv import load_dotenv

from backend.core.config import ROOT

load_dotenv(ROOT / ".env")

PRODUCTION = os.environ.get("MEDFLOW_ENV") == "production"
ORIGINS = set(
    os.environ.get(
        "MEDFLOW_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000,"
        "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
)
if PRODUCTION and (
    "MEDFLOW_ORIGINS" not in os.environ
    or any(not origin.startswith("https://") for origin in ORIGINS)
):
    raise RuntimeError("Production requires explicit HTTPS MEDFLOW_ORIGINS.")

SESSION_COOKIE = "__Host-medflow_session" if PRODUCTION else "medflow_session"
PREAUTH_COOKIE = "__Host-medflow_preauth" if PRODUCTION else "medflow_preauth"
