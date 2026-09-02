"""Per-IP sliding-window rate limit for write endpoints."""

import time
from collections import deque

from app.constants import (
    RATE_LIMIT_EVENTS_MAX_REQUESTS,
    RATE_LIMIT_EVENTS_PATHS,
    RATE_LIMIT_EVENTS_WINDOW_SECONDS,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_MAX_TRACKED_IPS,
    RATE_LIMIT_WINDOW_SECONDS,
    RATE_LIMIT_WRITE_METHODS,
)
from utils.http.response import json_error

# Cloudflare sets this on every edge request; local dev (pywrangler dev)
# often lacks it, so unidentified traffic shares one fallback bucket.
_UNKNOWN_IP = "unknown"

_buckets: dict[str, deque[float]] = {}
_event_buckets: dict[str, deque[float]] = {}


def _sweep(buckets: dict[str, deque[float]], cutoff: float) -> None:
    """Drop IP entries whose whole window has aged out. Bounds dict growth on
    a long-lived isolate without paying the cost on every request."""
    stale = [ip for ip, bucket in buckets.items() if not bucket or bucket[-1] < cutoff]
    for ip in stale:
        del buckets[ip]


def _check(buckets: dict[str, deque[float]], ip: str, max_requests: int, window_seconds: int) -> str | None:
    """Slide the window on `ip`'s bucket; return a retry-after message once over limit."""
    now = time.time()
    cutoff = now - window_seconds

    if len(buckets) > RATE_LIMIT_MAX_TRACKED_IPS:
        _sweep(buckets, cutoff)

    bucket = buckets.setdefault(ip, deque())

    while bucket and bucket[0] < cutoff:
        bucket.popleft()

    if len(bucket) >= max_requests:
        retry_after = max(1, int(bucket[0] + window_seconds - now) + 1)
        return f"Too many requests. Wait {retry_after}s and try again."

    bucket.append(now)
    return None


def check_rate_limit(request, method: str, path: str = ""):
    if method not in RATE_LIMIT_WRITE_METHODS:
        return None

    ip = request.headers.get("CF-Connecting-IP") or _UNKNOWN_IP

    if path in RATE_LIMIT_EVENTS_PATHS:
        message = _check(_event_buckets, ip, RATE_LIMIT_EVENTS_MAX_REQUESTS, RATE_LIMIT_EVENTS_WINDOW_SECONDS)
    else:
        message = _check(_buckets, ip, RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)

    return json_error(message, 429, code="RATE_LIMITED") if message else None
