"""
Router
Route table mapping (method, path) to handlers.
"""

import asyncio
import re
import time

from api.middleware.session_auth import get_session_user_uid
from api.routes import auth, events
from api.routes import kurls as kurls_routes
from api.services import urls as kurl_service
from app.config import DESCRIPTION, NAME, VERSION
from clients import cache
from clients.platforms import apple, deezer, spotify, tidal
from utils.http.response import json_error, json_response, parse_json_body

_routes = []
_start_time = time.time()


def route(method: str, pattern: str):
    regex = re.compile("^" + re.sub(r":(\w+)", r"(?P<\1>[^/]+)", pattern) + "$")

    def decorator(fn):
        _routes.append((method, regex, fn))
        return fn

    return decorator


def _uptime() -> float:
    return round(time.time() - _start_time, 2)


# System routes


@route("GET", "/")
@route("GET", "/api")
@route("GET", "/api/info")
async def _api_info(db, request, **kwargs):
    return json_response(
        {
            "status": "OK",
            "service": NAME,
            "version": VERSION,
            "description": DESCRIPTION,
            "message": f"{NAME} is live...",
            "uptime_seconds": _uptime(),
        }
    )


@route("GET", "/api/healthz")
async def _health(db, request, **kwargs):
    return json_response(
        {
            "status": "healthy",
            "service": NAME,
            "uptime_seconds": _uptime(),
        }
    )


@route("GET", "/api/readyz")
async def _readyz(db, request, **kwargs):
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

    return json_response(
        {
            "status": "ready" if not failed else "degraded",
            "service": NAME,
            "uptime_seconds": _uptime(),
            "checks": results,
        },
        status=503 if failed else 200,
    )


# Kurl endpoint


@route("POST", "/api/kurl")
async def _post_kurl(db, request, **kwargs):
    body = await parse_json_body(request)
    url = body.get("url")
    target_platform = body.get("target_platform")
    no_cache = bool(body.get("no_cache"))

    if not url or not target_platform:
        return json_error(
            "url and target_platform are required", 400, code="INVALID_REQUEST"
        )

    # Public endpoint regardless of login -- a session, if present, only
    # adds best-effort history recording on top of the same result.
    user_uid = get_session_user_uid(request)
    return await kurl_service.kurl(str(url), target_platform, no_cache=no_cache, db=db, user_uid=user_uid)


# Auth endpoints (accounts are optional -- kurling never requires one)


@route("POST", "/api/auth/signup")
async def _auth_signup(db, request, **kwargs):
    return await auth.signup(db, request)


@route("POST", "/api/auth/login")
async def _auth_login(db, request, **kwargs):
    return await auth.login(db, request)


@route("GET", "/api/auth/profile")
async def _auth_get_profile(db, request, **kwargs):
    return await auth.get_profile(db, request)


@route("PATCH", "/api/auth/profile")
async def _auth_update_profile(db, request, **kwargs):
    return await auth.update_profile(db, request)


# Kurl history (signed-in users only)


@route("GET", "/api/kurls")
async def _list_kurls(db, request, **kwargs):
    return await kurls_routes.list_kurls(db, request)


# Event endpoints


@route("POST", "/api/events")
async def _create_event(db, request, **kwargs):
    return await events.create_event(db, request)


@route("GET", "/api/events/summary")
async def _events_summary(db, request, **kwargs):
    return await events.get_summary(db, request)


@route("GET", "/api/events/approx-pairs")
async def _events_approx_pairs(db, request, **kwargs):
    return await events.get_approx_pairs(db, request)


# Resolve


async def resolve(db, method: str, path: str, request):
    for route_method, regex, handler in _routes:
        if method != route_method:
            continue
        match = regex.match(path)
        if match:
            return await handler(db, request, **match.groupdict())

    return json_error("Not found", 404, code="NOT_FOUND")


# Readiness probes


async def _check_cache() -> tuple:
    if cache._kv:
        return "cache", {"status": "healthy"}
    return "cache", {"status": "skipped", "reason": "no KV binding"}


async def _check_client(name, client, probe) -> tuple:
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
    await spotify._get_token()


async def _probe_apple():
    apple._generate_token()


async def _probe_deezer():
    await deezer.get_track("3135556")


async def _probe_tidal():
    await tidal._get_token()
