PLATFORMS = {
    "spotify",
    "appleMusic",
    "youtubeMusic",
    "soundcloud",
    "beatport",
    "bandcamp",
    "amazonMusic",
    "tidal",
    "deezer",
}

PLATFORM_NAMES = {
    "spotify": "Spotify",
    "appleMusic": "Apple Music",
    "youtubeMusic": "YouTube Music",
    "soundcloud": "SoundCloud",
    "beatport": "Beatport",
    "bandcamp": "Bandcamp",
    "amazonMusic": "Amazon Music",
    "tidal": "Tidal",
    "deezer": "Deezer",
}

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://kurl.online",
    "https://www.kurl.online",
]

"""
URL templates per platform.

Lookup: URL_TEMPLATES[platform][kind] where kind in
{track, album, artist, search, track_in_album}.

track_in_album is for Apple Music / Amazon where a track URL embeds its
parent album ID. Falls back to the plain track template when no album_id
is known.

Placeholders supported: {id}, {album_id}, {country}, {query}. Unused
placeholders in a given template are ignored by str.format.
"""
URL_TEMPLATES = {
    "spotify": {
        "track": "https://open.spotify.com/track/{id}",
        "album": "https://open.spotify.com/album/{id}",
        "artist": "https://open.spotify.com/artist/{id}",
        "search": "https://open.spotify.com/search/{query}",
    },
    "appleMusic": {
        "track": "https://music.apple.com/{country}/song/_/{id}",
        "track_in_album": "https://music.apple.com/{country}/album/_/{album_id}?i={id}",
        "album": "https://music.apple.com/{country}/album/_/{id}",
        "artist": "https://music.apple.com/{country}/artist/_/{id}",
        "search": "https://music.apple.com/us/search?term={query}",
    },
    "youtubeMusic": {
        "track": "https://music.youtube.com/watch?v={id}",
        "search": "https://music.youtube.com/search?q={query}",
    },
    "soundcloud": {
        "track": "https://soundcloud.com/{id}",
        "album": "https://soundcloud.com/{id}",
        "artist": "https://soundcloud.com/{id}",
        "search": "https://soundcloud.com/search?q={query}",
    },
    "beatport": {
        "track": "https://www.beatport.com/track/_/{id}",
        "album": "https://www.beatport.com/release/_/{id}",
        "artist": "https://www.beatport.com/artist/_/{id}",
        "search": "https://www.beatport.com/search?q={query}",
    },
    "bandcamp": {
        "track": "https://{id}",
        "album": "https://{id}",
        "artist": "https://{id}.bandcamp.com",
        "search": "https://bandcamp.com/search?q={query}",
    },
    "amazonMusic": {
        "track": "https://music.amazon.com/albums/{id}",
        "track_in_album": "https://music.amazon.com/albums/{album_id}?trackAsin={id}",
        "album": "https://music.amazon.com/albums/{id}",
        "artist": "https://music.amazon.com/artists/{id}",
        "search": "https://music.amazon.com/search/{query}",
    },
    "tidal": {
        "track": "https://tidal.com/track/{id}",
        "album": "https://tidal.com/album/{id}",
        "artist": "https://tidal.com/artist/{id}",
        "search": "https://tidal.com/search/{query}",
    },
    "deezer": {
        "track": "https://www.deezer.com/track/{id}",
        "album": "https://www.deezer.com/album/{id}",
        "artist": "https://www.deezer.com/artist/{id}",
        "search": "https://www.deezer.com/search/{query}",
    },
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

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

SOUNDCLOUD_API_BASE = "https://api.soundcloud.com"
SOUNDCLOUD_TOKEN_URL = "https://api.soundcloud.com/oauth2/token"

TIDAL_TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
TIDAL_API_BASE = "https://openapi.tidal.com/v2"
TIDAL_ACCEPT_HEADER = "application/vnd.api+json"

DEEZER_API_BASE = "https://api.deezer.com"

DEFAULT_COUNTRY = "US"
DEFAULT_STOREFRONT = "us"

CLIENT_TIMEOUT = 10.0
SCRAPER_TIMEOUT = 5.0
