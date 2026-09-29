import re

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.core.config import ROOT

DIST = ROOT / "frontend" / "dist"
router = APIRouter()


@router.get("/api/frontend-version", include_in_schema=False)
def frontend_version():
    index = DIST / "index.html"
    if not index.exists():
        return {"assets": []}
    assets = re.findall(
        r'(?:src|href)="(/assets/[^"]+\.(?:js|css))"', index.read_text(encoding="utf-8")
    )
    return {"assets": sorted(set(assets))}


def favicon():
    return FileResponse(DIST / "favicon.svg", media_type="image/svg+xml")


def frontend(path: str):
    if path.startswith("api/"):
        raise HTTPException(404)
    return FileResponse(DIST / "index.html", headers={"Cache-Control": "no-store"})


def register_frontend(app: FastAPI) -> None:
    app.include_router(router)
    if DIST.exists():
        app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")
        app.add_api_route("/favicon.svg", favicon, include_in_schema=False)
        app.add_api_route("/{path:path}", frontend, include_in_schema=False)
