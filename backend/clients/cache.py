from redis.asyncio import Redis

from app.config import settings
from utils.logging import get_logger

logger = get_logger()

_client: Redis | None = None


async def connect():
    global _client
    if not settings.REDIS_URL:
        logger.info("No REDIS_URL set — caching disabled")
        return
    try:
        _client = Redis.from_url(settings.REDIS_URL)
        await _client.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning("Redis unavailable, running without cache: %s", e)
        _client = None


async def disconnect():
    global _client
    if _client:
        await _client.aclose()
        _client = None


async def get(key: str) -> str | None:
    if not _client:
        return None
    try:
        return await _client.get(key)
    except Exception:
        return None


async def set(key: str, value: str, ttl: int | None = None) -> None:
    if not _client:
        return
    try:
        await _client.set(key, value, ex=ttl or settings.CACHE_TTL_SECONDS)
    except Exception:
        pass
