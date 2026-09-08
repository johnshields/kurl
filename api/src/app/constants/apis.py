"""External API base URLs, auth endpoints, scrape targets."""

# Streaming platform APIs.
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_EMBED_URL = "https://open.spotify.com/embed/track/{id}"

APPLE_API_BASE = "https://api.music.apple.com/v1"
APPLE_TOKEN_LIFETIME = 3600 * 12

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_OEMBED_URL = "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={id}&format=json"

SOUNDCLOUD_API_BASE = "https://api.soundcloud.com"
SOUNDCLOUD_TOKEN_URL = "https://api.soundcloud.com/oauth2/token"
SOUNDCLOUD_AUTHORIZE_URL = "https://secure.soundcloud.com/authorize"
SOUNDCLOUD_OAUTH_TOKEN_URL = "https://secure.soundcloud.com/oauth/token"

TIDAL_TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
TIDAL_API_BASE = "https://openapi.tidal.com/v2"
TIDAL_ACCEPT_HEADER = "application/vnd.api+json"

DEEZER_API_BASE = "https://api.deezer.com"
DEEZER_AUTHORIZE_URL = "https://connect.deezer.com/oauth/auth.php"
DEEZER_TOKEN_URL = "https://connect.deezer.com/oauth/access_token.php"

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

# Resolver endpoints (rescue path).
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
LASTFM_TRACK_URL = "https://www.last.fm/music/{artist}/_/{title}"
BANDCAMP_SEARCH_URL = "https://bandcamp.com/api/bcsearch_public_api/1/autocomplete_elastic"
GENIUS_API_BASE = "https://api.genius.com"
DDG_SEARCH_URL = "https://duckduckgo.com/html/?q={query}"

# Regional defaults.
DEFAULT_COUNTRY = "US"
DEFAULT_STOREFRONT = "us"
