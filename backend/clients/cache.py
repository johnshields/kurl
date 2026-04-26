"""
Cache layer (Cloudflare KV)
Falls back to no-op if no KV binding is available.
"""

from app.config import settings
from utils.logging import get_logger

logger = get_logger()

_kv = None


def init_kv(kv_binding):
    """Set the KV namespace binding. Called from the Workers entry point."""
    global _kv
    if kv_binding and not _kv:
        _kv = kv_binding
        logger.info("KV cache initialised")


async def connect():
    """No-op — KV is bound at request time, not via lifespan."""
    if not _kv:
        logger.info("No KV binding — caching disabled")


async def disconnect():
    """No-op — KV has no connection to close."""
    pass


async def get(key: str) -> str | None:
    if not _kv:
        return None
    try:
        return await _kv.get(key)
    except Exception:
        return None


async def set(key: str, value: str, ttl: int | None = None) -> None:
    if not _kv:
        return
    try:
        await _kv.put(key, value, expiration=ttl or settings.CACHE_TTL_SECONDS)
    except Exception:
        pass
