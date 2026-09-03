"""
Session Auth Middleware
Verifies a per-user session token (Bearer JWT), separate from the shared
API-key check in auth.py -- that gates admin/analytics endpoints, this
gates account endpoints. get_session_user_uid never errors, so callers on
routes where login is optional (e.g. /api/kurl) can treat a missing/invalid
token as "anonymous" rather than a failure.
"""

from app.config import settings
from utils.http.response import json_error
from utils.session import verify_session_token


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
