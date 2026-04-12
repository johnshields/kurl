from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    REDIS_URL: str | None = None
    ODESLI_BASE_URL: str = "https://api.song.link/v1-alpha.1/links"
    ODESLI_API_KEY: str | None = None
    CACHE_TTL_SECONDS: int = 86400


settings = Settings()
