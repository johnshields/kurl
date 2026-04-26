"""
kurl API
Cloudflare Workers entrypoint.
"""

import time

from workers import WorkerEntrypoint

from api.router import resolve
from clients import cache
from utils.logging import get_logger
from utils.response import json_error, parse_path, preflight

logger = get_logger()

_started_at = time.time()


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        method = request.method
        path = parse_path(request.url)
        start = time.time()

        if method == "OPTIONS":
            return preflight()

        try:
            kv = getattr(self.env, "CACHE", None)
            cache.init_kv(kv)

            response = await resolve(method, path, request)
        except Exception as e:
            logger.error("Unhandled exception on [%s] %s: %s", method, path, e)
            response = json_error("Internal server error", 500)

        duration = round((time.time() - start) * 1000, 1)
        logger.info("%s %s %s %sms", method, path, response.status, duration)

        return response
