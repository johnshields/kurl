from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import NAME, VERSION, DESCRIPTION, ENVIRONMENT, HOST, PORT, BASE_URL, CORS_ORIGINS
from app.constants import ERROR_MESSAGES, OPENAPI_TAGS
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
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.root_router)
app.include_router(system.router)
app.include_router(urls.router)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return error(ERROR_MESSAGES["INTERNAL_ERROR"], status_code=500)


if __name__ == "__main__":
    logger.info("%s booting up (%s)...", NAME, ENVIRONMENT)
    logger.info("%s running at %s", NAME, BASE_URL)
    uvicorn.run("main:app", host=HOST, port=PORT, reload=not ENVIRONMENT == "production")
