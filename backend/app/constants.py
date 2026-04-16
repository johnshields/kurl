PLATFORMS = {
    "spotify",
    "appleMusic",
    "youtubeMusic",
    "deezer",
    "tidal",
    "amazonMusic",
    "pandora",
}

PLATFORM_NAMES = {
    "spotify": "Spotify",
    "appleMusic": "Apple Music",
    "youtubeMusic": "YouTube Music",
    "deezer": "Deezer",
    "tidal": "Tidal",
    "amazonMusic": "Amazon Music",
    "pandora": "Pandora",
}

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://kurlshare.com",
    "https://www.kurlshare.com",
]

OPENAPI_TAGS = [
    {"name": "System", "description": "Health checks, API information, and system status"},
    {"name": "URLs", "description": "Cross-platform URL resolution"},
]

ERROR_MESSAGES = {
    "UNKNOWN_PLATFORM": "Unknown platform",
    "PLATFORM_NOT_FOUND": "No URL found for this track",
    "ODESLI_ERROR": "Odesli API error",
    "INTERNAL_ERROR": "Internal server error",
    "SEARCH_URL": "That's a search URL — paste the link to a specific track",
}

SEARCH_URL_TEMPLATES = {
    "spotify": "https://open.spotify.com/search/{query}",
    "appleMusic": "https://music.apple.com/search?term={query}",
    "youtubeMusic": "https://music.youtube.com/search?q={query}",
}

SPOTIFY_EMBED_URL = "https://open.spotify.com/embed/track/{id}"

SCRAPER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

"""
Platform API endpoints
Base URLs and auth endpoints for direct ISRC/UPC resolution.
"""

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

APPLE_API_BASE = "https://api.music.apple.com/v1"
APPLE_TOKEN_LIFETIME = 3600 * 12

DEEZER_API_BASE = "https://api.deezer.com"

TIDAL_TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
TIDAL_API_BASE = "https://openapi.tidal.com"
TIDAL_ACCEPT_HEADER = "application/vnd.tidal.v1+json"

DEFAULT_COUNTRY = "US"
DEFAULT_STOREFRONT = "us"

CLIENT_TIMEOUT = 10.0
