"""
App configuration
Reads from environment variables. Works on both Cloudflare Workers
(env bindings) and local dev (os.environ / .env file).
"""

import os

from app.constants import ALLOWED_ORIGINS

NAME = "kurl_api"
VERSION = "0.1.0"
DESCRIPTION = "Share any song. To anyone. On any streaming service."

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
BASE_URL = os.getenv("BASE_URL", f"http://localhost:{PORT}").rstrip("/")

CORS_ORIGINS = (
    [o.strip() for o in os.getenv("CORS_ORIGINS").split(",") if o.strip()]
    if os.getenv("CORS_ORIGINS")
    else ALLOWED_ORIGINS
)


def is_production() -> bool:
    return ENVIRONMENT == "production"


class Settings:
    """Lazy settings that read from os.environ on access."""

    def _get(self, key: str, default: str | None = None) -> str | None:
        return os.getenv(key, default)

    def _get_int(self, key: str, default: int) -> int:
        return int(os.getenv(key, str(default)))

    @property
    def REDIS_URL(self) -> str | None:
        return self._get("REDIS_URL")

    @property
    def ODESLI_BASE_URL(self) -> str:
        return self._get("ODESLI_BASE_URL", "https://api.song.link/v1-alpha.1/links")

    @property
    def ODESLI_API_KEY(self) -> str | None:
        return self._get("ODESLI_API_KEY")

    @property
    def GENIUS_ACCESS_TOKEN(self) -> str | None:
        return self._get("GENIUS_ACCESS_TOKEN")

    @property
    def CACHE_TTL_SECONDS(self) -> int:
        return self._get_int("CACHE_TTL_SECONDS", 86400)

    # Spotify (OAuth client credentials)
    @property
    def SPOTIFY_API_ENABLED(self) -> bool:
        return self._get("SPOTIFY_API_ENABLED", "false") == "true"

    @property
    def SPOTIFY_CLIENT_ID(self) -> str | None:
        return self._get("SPOTIFY_CLIENT_ID")

    @property
    def SPOTIFY_CLIENT_SECRET(self) -> str | None:
        return self._get("SPOTIFY_CLIENT_SECRET")

    # Apple Music (JWT via MusicKit)
    @property
    def APPLE_TEAM_ID(self) -> str | None:
        return self._get("APPLE_TEAM_ID")

    @property
    def APPLE_KEY_ID(self) -> str | None:
        return self._get("APPLE_KEY_ID")

    @property
    def APPLE_PRIVATE_KEY(self) -> str | None:
        return self._get("APPLE_PRIVATE_KEY")

    # Tidal (OAuth client credentials)
    @property
    def TIDAL_CLIENT_ID(self) -> str | None:
        return self._get("TIDAL_CLIENT_ID")

    @property
    def TIDAL_CLIENT_SECRET(self) -> str | None:
        return self._get("TIDAL_CLIENT_SECRET")

    # YouTube Data API v3 (API key)
    @property
    def YOUTUBE_API_KEY(self) -> str | None:
        return self._get("YOUTUBE_API_KEY")

    # SoundCloud (OAuth 2.1 client credentials)
    @property
    def SOUNDCLOUD_CLIENT_ID(self) -> str | None:
        return self._get("SOUNDCLOUD_CLIENT_ID")

    @property
    def SOUNDCLOUD_CLIENT_SECRET(self) -> str | None:
        return self._get("SOUNDCLOUD_CLIENT_SECRET")


settings = Settings()
