"""
Auth Middleware
API key validation for protected endpoints.
"""

import hmac

from utils.http.response import json_error

PUBLIC_PATHS = {
    "/",
    "/api",
    "/api/info",
    "/api/healthz",
    "/api/kurl",
    "/api/events",
}


def authenticate(request, path: str, api_key: str | None):
    if path in PUBLIC_PATHS:
        return None

    if not api_key:
        return None

    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not token:
        token = request.headers.get("X-API-Key", "").strip()

    if not token:
        return json_error("Authentication required.", 401, code="AUTH_REQUIRED")

    if not hmac.compare_digest(token, api_key):
        return json_error("Invalid API key.", 401, code="AUTH_INVALID")

    return None
