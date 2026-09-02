"""In-memory rate limit for write endpoints."""

import time
from collections import deque

from app.constants import (
    RATE_LIMIT_EVENTS_MAX_REQUESTS,
    RATE_LIMIT_EVENTS_PATHS,
    RATE_LIMIT_EVENTS_WINDOW_SECONDS,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    RATE_LIMIT_WRITE_METHODS,
)
from utils.http.response import json_error

_requests: deque[float] = deque()
_event_requests: deque[float] = deque()


def _check(bucket: deque[float], max_requests: int, window_seconds: int) -> str | None:
    """Slide the window on `bucket`; return a retry-after message once over limit."""
    now = time.time()
    cutoff = now - window_seconds

    while bucket and bucket[0] < cutoff:
        bucket.popleft()

    if len(bucket) >= max_requests:
        retry_after = max(1, int(bucket[0] + window_seconds - now) + 1)
        return f"Too many requests. Wait {retry_after}s and try again."

    bucket.append(now)
    return None


def check_rate_limit(method: str, path: str = ""):
    if method not in RATE_LIMIT_WRITE_METHODS:
        return None

    if path in RATE_LIMIT_EVENTS_PATHS:
        message = _check(_event_requests, RATE_LIMIT_EVENTS_MAX_REQUESTS, RATE_LIMIT_EVENTS_WINDOW_SECONDS)
    else:
        message = _check(_requests, RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)

    return json_error(message, 429, code="RATE_LIMITED") if message else None
