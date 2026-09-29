from fastapi import FastAPI

from backend.http.frontend import register_frontend
from backend.http.middleware import api_security
from backend.modules.accounts.router import router as admin_router
from backend.modules.analytics.router import router as analytics_router
from backend.modules.auth.config import PRODUCTION
from backend.modules.auth.router import router as auth_router
from backend.modules.briefings.router import router as briefings_router
from backend.modules.hospitals.router import router as hospitals_router
from backend.modules.predictions.router import router as predictions_router
from backend.modules.system.router import router as system_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="MedFlow AI API",
        version="2.0.0",
        docs_url=None if PRODUCTION else "/docs",
        redoc_url=None if PRODUCTION else "/redoc",
        openapi_url=None if PRODUCTION else "/openapi.json",
    )
    application.middleware("http")(api_security)
    for router in (
        auth_router,
        admin_router,
        analytics_router,
        hospitals_router,
        predictions_router,
        briefings_router,
        system_router,
    ):
        application.include_router(router)
    register_frontend(application)
    return application


app = create_app()
