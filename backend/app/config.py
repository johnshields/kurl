import os

from pydantic_settings import BaseSettings

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


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    REDIS_URL: str | None = None
    ODESLI_BASE_URL: str = "https://api.song.link/v1-alpha.1/links"
    ODESLI_API_KEY: str | None = None
    CACHE_TTL_SECONDS: int = 86400

    # Spotify (OAuth client credentials)
    SPOTIFY_CLIENT_ID: str | None = None
    SPOTIFY_CLIENT_SECRET: str | None = None

    # Apple Music (JWT via MusicKit)
    APPLE_TEAM_ID: str | None = None
    APPLE_KEY_ID: str | None = None
    APPLE_PRIVATE_KEY: str | None = None

    # Tidal (OAuth client credentials)
    TIDAL_CLIENT_ID: str | None = None
    TIDAL_CLIENT_SECRET: str | None = None

    # Deezer requires no credentials


settings = Settings()
