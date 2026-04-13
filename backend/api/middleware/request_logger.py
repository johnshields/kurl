import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from utils.logging import get_logger

logger = get_logger()


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = round((time.perf_counter() - start) * 1000, 1)

        logger.info(
            "%s %s %s %sms",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )

        response.headers["X-Process-Time"] = str(duration)
        return response
