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
    "deezer": "https://www.deezer.com/search/{query}",
    "tidal": "https://tidal.com/search/{query}",
    "amazonMusic": "https://music.amazon.com/search/{query}",
    "pandora": "https://www.pandora.com/search/{query}",
}

"""
Canonical URL templates
Used for rebuilding a platform URL from a parsed entity (track/album/artist id).
Apple Music and Amazon tracks live inside albums, so use TRACK_WITH_ALBUM when
album_id is known.
"""
TRACK_URL_TEMPLATES = {
    "spotify": "https://open.spotify.com/track/{id}",
    "appleMusic": "https://music.apple.com/{country}/song/_/{id}",
    "deezer": "https://www.deezer.com/track/{id}",
    "tidal": "https://tidal.com/track/{id}",
    "youtubeMusic": "https://music.youtube.com/watch?v={id}",
    "amazonMusic": "https://music.amazon.com/albums/{id}",
}

TRACK_WITH_ALBUM_URL_TEMPLATES = {
    "appleMusic": "https://music.apple.com/{country}/album/_/{album_id}?i={id}",
    "amazonMusic": "https://music.amazon.com/albums/{album_id}?trackAsin={id}",
}

ALBUM_URL_TEMPLATES = {
    "spotify": "https://open.spotify.com/album/{id}",
    "appleMusic": "https://music.apple.com/{country}/album/_/{id}",
    "deezer": "https://www.deezer.com/album/{id}",
    "tidal": "https://tidal.com/album/{id}",
    "amazonMusic": "https://music.amazon.com/albums/{id}",
}

ARTIST_URL_TEMPLATES = {
    "spotify": "https://open.spotify.com/artist/{id}",
    "appleMusic": "https://music.apple.com/{country}/artist/_/{id}",
    "deezer": "https://www.deezer.com/artist/{id}",
    "tidal": "https://tidal.com/artist/{id}",
    "amazonMusic": "https://music.amazon.com/artists/{id}",
}

SPOTIFY_EMBED_URL = "https://open.spotify.com/embed/track/{id}"

YOUTUBE_OEMBED_URL = "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={id}&format=json"

SCRAPER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
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
TIDAL_API_BASE = "https://openapi.tidal.com/v2"
TIDAL_ACCEPT_HEADER = "application/vnd.api+json"

DEFAULT_COUNTRY = "US"
DEFAULT_STOREFRONT = "us"

CLIENT_TIMEOUT = 10.0
SCRAPER_TIMEOUT = 5.0
