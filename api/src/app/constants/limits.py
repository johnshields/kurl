"""Rate-limit, retry, backoff knobs."""

# In-memory, per-IP write-endpoint rate limit.
RATE_LIMIT_WRITE_METHODS = {"POST", "PATCH", "DELETE"}
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60

# Above this many tracked IPs, sweep entries whose window aged out --
# bounds dict growth on a long-lived isolate.
RATE_LIMIT_MAX_TRACKED_IPS = 5000

# Looser bucket for analytics events -- a page load fires several, so its
# own bucket keeps them off the write-endpoint limit above.
RATE_LIMIT_EVENTS_PATHS = {"/api/events"}
RATE_LIMIT_EVENTS_MAX_REQUESTS = 60
RATE_LIMIT_EVENTS_WINDOW_SECONDS = 60

# Odesli retry policy.
ODESLI_MAX_RETRIES = 3
ODESLI_BACKOFF_SECONDS = (1, 2, 4)

ISRC_CACHE_POSITIVE_TTL = 86400
ISRC_CACHE_NEGATIVE_TTL = 900
