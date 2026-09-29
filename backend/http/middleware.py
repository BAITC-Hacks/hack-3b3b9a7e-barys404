import psycopg
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from backend.modules.auth.dependencies import check_csrf


async def api_security(request: Request, call_next):
    try:
        if request.url.path.startswith("/api/"):
            if request.method not in {"GET", "HEAD", "OPTIONS"}:
                await run_in_threadpool(check_csrf, request)
        response = await call_next(request)
    except HTTPException as error:
        response = JSONResponse({"detail": error.detail}, status_code=error.status_code)
    except (psycopg.Error, RuntimeError):
        response = JSONResponse(
            {"detail": "Сервис временно недоступен. Повторите попытку позже."},
            status_code=503,
        )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    return response
