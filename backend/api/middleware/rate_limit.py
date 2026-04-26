"""
Rate Limit Middleware
Simple in-memory rate limiting for write endpoints.
"""

import time

from utils.response import json_error

WRITE_METHODS = {"POST", "PATCH", "DELETE"}
RATE_LIMIT_EXEMPT_PATHS = {"/api/events"}
MAX_REQUESTS = 10
WINDOW_SECONDS = 60

_requests = []


def check_rate_limit(method: str, path: str = ""):
    if method not in WRITE_METHODS:
        return None

    if path in RATE_LIMIT_EXEMPT_PATHS:
        return None

    now = time.time()
    cutoff = now - WINDOW_SECONDS

    while _requests and _requests[0] < cutoff:
        _requests.pop(0)

    if len(_requests) >= MAX_REQUESTS:
        return json_error("Rate limit exceeded. Try again later.", 429)

    _requests.append(now)
    return None
