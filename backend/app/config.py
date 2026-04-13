import os

from pydantic_settings import BaseSettings

NAME = "kurl_api"
VERSION = "0.1.0"
DESCRIPTION = "Share any song. To anyone. On any streaming service."

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
BASE_URL = os.getenv("BASE_URL", f"http://localhost:{PORT}").rstrip("/")


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    REDIS_URL: str | None = None
    ODESLI_BASE_URL: str = "https://api.song.link/v1-alpha.1/links"
    ODESLI_API_KEY: str | None = None
    CACHE_TTL_SECONDS: int = 86400


settings = Settings()
