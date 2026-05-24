"""In-memory rate limit for write endpoints."""

import time
from collections import deque

from app.constants import (
    RATE_LIMIT_EXEMPT_PATHS,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    RATE_LIMIT_WRITE_METHODS,
)
from utils.http.response import json_error

_requests: deque[float] = deque()


def check_rate_limit(method: str, path: str = ""):
    if method not in RATE_LIMIT_WRITE_METHODS or path in RATE_LIMIT_EXEMPT_PATHS:
        return None

    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS

    while _requests and _requests[0] < cutoff:
        _requests.popleft()

    if len(_requests) >= RATE_LIMIT_MAX_REQUESTS:
        retry_after = max(1, int(_requests[0] + RATE_LIMIT_WINDOW_SECONDS - now) + 1)
        return json_error(f"Too many requests. Wait {retry_after}s and try again.", 429, code="RATE_LIMITED")

    _requests.append(now)
    return None
