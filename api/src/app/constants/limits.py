"""Rate-limit, retry, backoff knobs."""

# In-memory write-endpoint rate limit.
RATE_LIMIT_WRITE_METHODS = {"POST", "PATCH", "DELETE"}
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60

# Separate, looser bucket for analytics events -- a single page load fires
# several (page_view, kurl, kurl_success, platform_select, open_result), so
# they'd blow through the write-endpoint limit above. Own bucket keeps them
# capped without competing with /api/kurl traffic.
RATE_LIMIT_EVENTS_PATHS = {"/api/events"}
RATE_LIMIT_EVENTS_MAX_REQUESTS = 60
RATE_LIMIT_EVENTS_WINDOW_SECONDS = 60

# Odesli retry policy.
ODESLI_MAX_RETRIES = 3
ODESLI_BACKOFF_SECONDS = (1, 2, 4)
