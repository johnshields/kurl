import time

from fastapi import APIRouter, Request

from api import templates
from app.config import NAME, VERSION, DESCRIPTION

root_router = APIRouter()
router = APIRouter(prefix="/api")

_start_time = time.time()


def _uptime() -> float:
    return round(time.time() - _start_time, 2)


def _info() -> dict:
    return {
        "status": "OK",
        "service": NAME,
        "version": VERSION,
        "description": DESCRIPTION,
        "message": f"{NAME} is live...",
        "uptime_seconds": _uptime(),
    }


@root_router.get("/", include_in_schema=False)
def root(request: Request):
    """Landing page — service info fetched client-side from /api."""
    return templates.TemplateResponse(request, "index.html", {"name": NAME})


@router.get("/", tags=["System"])
@router.get("/info", tags=["System"], include_in_schema=False)
def api_info():
    """Return service name, description, and uptime."""
    return _info()


@router.get("/healthz", tags=["System"])
def health_check():
    """Check service health and uptime."""
    return {
        "status": "healthy",
        "service": NAME,
        "uptime_seconds": _uptime(),
    }
