"""External API base URLs, auth endpoints, scrape targets."""

# Streaming platform APIs.
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_EMBED_URL = "https://open.spotify.com/embed/track/{id}"

APPLE_API_BASE = "https://api.music.apple.com/v1"
APPLE_TOKEN_LIFETIME = 3600 * 12

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_OEMBED_URL = "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={id}&format=json"

SOUNDCLOUD_API_BASE = "https://api.soundcloud.com"
SOUNDCLOUD_TOKEN_URL = "https://api.soundcloud.com/oauth2/token"

TIDAL_TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
TIDAL_API_BASE = "https://openapi.tidal.com/v2"
TIDAL_ACCEPT_HEADER = "application/vnd.api+json"

DEEZER_API_BASE = "https://api.deezer.com"

# Resolver endpoints (rescue path).
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
LASTFM_TRACK_URL = "https://www.last.fm/music/{artist}/_/{title}"
MUSICBRAINZ_API_BASE = "https://musicbrainz.org/ws/2"
MUSICBRAINZ_USER_AGENT = "kurl/1.0 (https://kurl.online)"

# Regional defaults.
DEFAULT_COUNTRY = "US"
DEFAULT_STOREFRONT = "us"
