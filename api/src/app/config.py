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
    def SPOTIFY_CLIENT_ID(self) -> str | None:
        return self._get("SPOTIFY_CLIENT_ID")

    @property
    def SPOTIFY_CLIENT_SECRET(self) -> str | None:
        return self._get("SPOTIFY_CLIENT_SECRET")

    # Spotify (OAuth authorization_code -- Sign in with Spotify)
    @property
    def SPOTIFY_REDIRECT_URI(self) -> str | None:
        """Must exactly match a redirect URI registered in the Spotify app dashboard."""
        return self._get("SPOTIFY_REDIRECT_URI")

    @property
    def SPOTIFY_APP_REDIRECT_URL(self) -> str:
        """Frontend URL the callback bounces the browser back to once done."""
        return self._get("SPOTIFY_APP_REDIRECT_URL", "https://kurl.online/settings")

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

    # SoundCloud (OAuth 2.1 authorization_code + PKCE -- Sign in with SoundCloud)
    @property
    def SOUNDCLOUD_REDIRECT_URI(self) -> str | None:
        """Must exactly match a redirect URI registered in the SoundCloud app dashboard."""
        return self._get("SOUNDCLOUD_REDIRECT_URI")

    @property
    def SOUNDCLOUD_APP_REDIRECT_URL(self) -> str:
        """Frontend URL the callback bounces the browser back to once done."""
        return self._get("SOUNDCLOUD_APP_REDIRECT_URL", "https://kurl.online/settings")

    # Google (OAuth authorization_code -- Sign in with YouTube). Separate
    # from YOUTUBE_API_KEY above, which is an unrelated Data API v3 key.
    @property
    def GOOGLE_CLIENT_ID(self) -> str | None:
        return self._get("GOOGLE_CLIENT_ID")

    @property
    def GOOGLE_CLIENT_SECRET(self) -> str | None:
        return self._get("GOOGLE_CLIENT_SECRET")

    @property
    def GOOGLE_REDIRECT_URI(self) -> str | None:
        """Must exactly match a redirect URI registered in the Google Cloud OAuth client."""
        return self._get("GOOGLE_REDIRECT_URI")

    @property
    def GOOGLE_APP_REDIRECT_URL(self) -> str:
        """Frontend URL the callback bounces the browser back to once done."""
        return self._get("GOOGLE_APP_REDIRECT_URL", "https://kurl.online/settings")

    # User accounts (session JWT signing key -- distinct from KURL_API_KEY)
    @property
    def SESSION_SECRET(self) -> str | None:
        return self._get("SESSION_SECRET")

    # AES-256-GCM key for encrypting stored OAuth tokens (64 hex chars / 32 bytes).
    @property
    def TOKEN_ENCRYPTION_KEY(self) -> str | None:
        return self._get("TOKEN_ENCRYPTION_KEY")

    # AES-256-GCM key for encrypting message bodies at rest (64 hex chars / 32 bytes).
    # Separate from TOKEN_ENCRYPTION_KEY -- different blast radius if one leaks.
    @property
    def MESSAGE_ENCRYPTION_KEY(self) -> str | None:
        return self._get("MESSAGE_ENCRYPTION_KEY")


settings = Settings()
