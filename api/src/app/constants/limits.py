"""Rate-limit, retry, backoff knobs."""

# In-memory write-endpoint rate limit.
RATE_LIMIT_WRITE_METHODS = {"POST", "PATCH", "DELETE"}
RATE_LIMIT_EXEMPT_PATHS = {"/api/events"}
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60

# Odesli retry policy.
ODESLI_MAX_RETRIES = 3
ODESLI_BACKOFF_SECONDS = (1, 2, 4)

# Short TTL for negative cache entries so repeat 404s skip the full pipeline.
NEGATIVE_CACHE_TTL_SECONDS = 600
