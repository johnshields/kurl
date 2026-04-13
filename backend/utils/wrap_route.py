import logging
from functools import wraps

from fastapi import HTTPException

logger = logging.getLogger("uvicorn.error")


def wrap_route(label: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger.info("%s request...", label)
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error("%s error: %s", label, e)
                raise
        return wrapper
    return decorator
