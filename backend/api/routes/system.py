import asyncio
import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api import render
from app.config import DESCRIPTION, NAME, VERSION
from clients import cache
from clients.platforms import apple, deezer, spotify, tidal
from utils.logging import get_logger

logger = get_logger()

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
def root():
    """Landing page — service info fetched client-side from /api."""
    return render("index.html", {"name": NAME})


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


@router.get("/readyz", tags=["System"])
async def readiness_check():
    """Check that all configured platform clients can reach their APIs.

    Returns 200 if all configured clients are reachable, 503 if any fail.
    Unconfigured clients are skipped (reported as 'skipped').
    """
    checks = await asyncio.gather(
        _check_cache(),
        _check_client("spotify", spotify, _probe_spotify),
        _check_client("appleMusic", apple, _probe_apple),
        _check_client("deezer", deezer, _probe_deezer),
        _check_client("tidal", tidal, _probe_tidal),
        return_exceptions=False,
    )

    results = dict(checks)
    failed = [k for k, v in results.items() if v["status"] == "unhealthy"]
    status_code = 503 if failed else 200

    return JSONResponse(
        {
            "status": "ready" if not failed else "degraded",
            "service": NAME,
            "uptime_seconds": _uptime(),
            "checks": results,
        },
        status_code=status_code,
    )


async def _check_cache() -> tuple[str, dict]:
    """Cache is optional -- unavailable is 'skipped', not a failure."""
    if cache._kv:
        return "cache", {"status": "healthy"}
    return "cache", {"status": "skipped", "reason": "no KV binding"}


async def _check_client(name: str, client, probe) -> tuple[str, dict]:
    """Run a platform client probe. Unconfigured clients are skipped."""
    if not client.is_configured():
        return name, {"status": "skipped", "reason": "no credentials"}
    try:
        await asyncio.wait_for(probe(), timeout=5.0)
        return name, {"status": "healthy"}
    except TimeoutError:
        return name, {"status": "unhealthy", "reason": "timeout after 5s"}
    except Exception as e:
        return name, {"status": "unhealthy", "reason": f"{type(e).__name__}: {str(e)[:100]}"}


async def _probe_spotify():
    """Fetch an access token -- proves creds + API reachability."""
    await spotify._get_token()


async def _probe_apple():
    """Generate a JWT -- proves the private key + team/key IDs work."""
    apple._generate_token()


async def _probe_deezer():
    """Hit a public endpoint -- Deezer has no auth."""
    await deezer.get_track("3135556")  # stable, well-known track


async def _probe_tidal():
    """Fetch an access token -- proves creds + API reachability."""
    await tidal._get_token()
