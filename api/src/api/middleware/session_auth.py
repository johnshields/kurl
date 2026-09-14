"""
Session Auth Middleware
Verifies a per-user session token (Bearer JWT); separate from the shared
admin API key checked by middleware.auth.
"""

from functools import wraps

from app.config import settings
from utils.auth.session import verify_session_token
from utils.http.response import json_error


def get_session_user_uid(request) -> str | None:
    if not settings.SESSION_SECRET:
        return None
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token:
        return None
    return verify_session_token(token, settings.SESSION_SECRET)


def require_session(request):
    user_uid = get_session_user_uid(request)
    if not user_uid:
        return None, json_error("Login required.", 401, code="AUTH_REQUIRED")
    return user_uid, None


def with_session(fn):
    """Route decorator: injects user_uid as the first arg after (db, request),
    or short-circuits with the 401 response."""

    @wraps(fn)
    async def wrapper(db, request, *args, **kwargs):
        user_uid, error = require_session(request)
        if error:
            return error
        return await fn(db, request, user_uid, *args, **kwargs)

    return wrapper
