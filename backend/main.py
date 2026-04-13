from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import NAME, VERSION, DESCRIPTION, HOST, PORT, BASE_URL
from app.constants import OPENAPI_TAGS
from api.middleware.request_logger import RequestLoggerMiddleware
from api.routes import system, urls
from clients import cache
from utils.logging import get_logger
from utils.responses import error

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache.connect()
    yield
    await cache.disconnect()


app = FastAPI(
    title=NAME,
    version=VERSION,
    description=DESCRIPTION,
    servers=[{"url": BASE_URL, "description": "API Server"}],
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)

app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(urls.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return error("Internal server error", status_code=500)


if __name__ == "__main__":
    logger.info("%s booting up...", NAME)
    logger.info("%s running at %s", NAME, BASE_URL)
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
