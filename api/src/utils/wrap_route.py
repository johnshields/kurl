from functools import wraps

from utils.errors import ApiError
from utils.logging import get_logger

logger = get_logger()


def wrap_route(label: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger.info("%s request...", label)
            try:
                return await func(*args, **kwargs)
            except ApiError as e:
                logger.warning("%s failed (%s): %s", label, e.status_code, e.detail)
                raise
            except Exception as e:
                logger.error("%s error: %s", label, e, exc_info=True)
                raise

        return wrapper

    return decorator
