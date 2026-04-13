from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import NAME, VERSION, DESCRIPTION, ENVIRONMENT, HOST, PORT, BASE_URL, CORS_ORIGINS
from app.constants import ERROR_MESSAGES, OPENAPI_TAGS
from api.middleware.request_logger import RequestLoggerMiddleware
from api.routes import docs, system, urls
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
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="public/static"), name="static")

app.include_router(system.root_router)
app.include_router(system.router)
app.include_router(urls.router)
app.include_router(docs.router)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("public/static/favicon.ico")


@app.get("/.well-known/apple-app-site-association", include_in_schema=False)
async def apple_app_site_association():
    return FileResponse(
        "public/.well-known/apple-app-site-association",
        media_type="application/json",
    )


@app.get("/.well-known/assetlinks.json", include_in_schema=False)
async def assetlinks():
    return FileResponse(
        "public/.well-known/assetlinks.json",
        media_type="application/json",
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return error(ERROR_MESSAGES["INTERNAL_ERROR"], status_code=500)


if __name__ == "__main__":
    logger.info("%s booting up (%s)...", NAME, ENVIRONMENT)
    logger.info("%s running at %s", NAME, BASE_URL)
    uvicorn.run("main:app", host=HOST, port=PORT, reload=not ENVIRONMENT == "production")
