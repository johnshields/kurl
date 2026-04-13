import time

from fastapi import APIRouter

from app.config import NAME, VERSION, DESCRIPTION

router = APIRouter(prefix="/api")

_start_time = time.time()


def _uptime() -> float:
    return round(time.time() - _start_time, 2)


@router.get("/", tags=["System"])
@router.get("/info", tags=["System"], include_in_schema=False)
def api_info():
    """Return service name, description, and uptime."""
    return {
        "status": "OK",
        "service": NAME,
        "version": VERSION,
        "description": DESCRIPTION,
        "message": f"{NAME} is live...",
        "uptime_seconds": _uptime(),
    }


@router.get("/healthz", tags=["System"])
def health_check():
    """Check service health and uptime."""
    return {
        "status": "healthy",
        "service": NAME,
        "uptime_seconds": _uptime(),
    }
