"""HTTP client timeouts, CORS, user agents."""

CLIENT_TIMEOUT = 10.0
SCRAPER_TIMEOUT = 5.0

SCRAPER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://kurl-web.pages.dev",
    "https://kurl.fromlost.com",
]

APP_BASE_URL = "https://kurl-web.pages.dev"
EMAIL_FROM = "kurl@fromlost.com"

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-API-Key, Authorization",
    "Access-Control-Allow-Credentials": "true",
}
