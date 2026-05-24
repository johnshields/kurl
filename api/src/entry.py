"""
kurl API
Cloudflare Workers entrypoint.
"""

import os
import time

from workers import WorkerEntrypoint

from api.middleware.auth import authenticate
from api.middleware.rate_limit import check_rate_limit
from api.router import resolve
from clients import cache
from utils.http.errors import ApiError
from utils.logging import get_logger
from utils.http.response import json_error, parse_path, preflight

logger = get_logger()

# Secret names to inject from Worker env into os.environ.
_SECRET_KEYS = [
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "TIDAL_CLIENT_ID",
    "TIDAL_CLIENT_SECRET",
    "APPLE_TEAM_ID",
    "APPLE_KEY_ID",
    "APPLE_PRIVATE_KEY",
    "ODESLI_API_KEY",
    "YOUTUBE_API_KEY",
    "SOUNDCLOUD_CLIENT_ID",
    "SOUNDCLOUD_CLIENT_SECRET",
]


def _inject_env(env):
    """Copy Worker secret bindings into os.environ so Settings/os.getenv works."""
    for key in _SECRET_KEYS:
        val = getattr(env, key, None)
        if val and key not in os.environ:
            os.environ[key] = str(val)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        method = request.method
        path = parse_path(request.url)
        start = time.time()

        if method == "OPTIONS":
            return preflight()

        try:
            _inject_env(self.env)

            db = getattr(self.env, "kurl", None)
            kv = getattr(self.env, "CACHE", None)
            api_key = getattr(self.env, "KURL_API_KEY", None)
            cache.init_kv(kv)

            auth_error = authenticate(request, path, api_key)
            if auth_error:
                return auth_error

            rate_error = check_rate_limit(method, path)
            if rate_error:
                return rate_error

            response = await resolve(db, method, path, request)
        except ApiError as e:
            logger.warning("ApiError on [%s] %s: %s", method, path, e.detail)
            response = json_error(e.detail, e.status_code, code=e.code)
        except Exception as e:
            logger.error("Unhandled exception on [%s] %s: %s", method, path, e)
            response = json_error("Internal server error", 500, code="INTERNAL_ERROR")

        duration = round((time.time() - start) * 1000, 1)
        logger.info("%s %s %s %sms", method, path, response.status, duration)

        return response
