import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.middleware.request_logger import RequestLoggerMiddleware
from api.routes import urls
from services import cache
from utils.response import create_error

VERSION = "0.1.0"
started_at = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache.connect()
    yield
    await cache.disconnect()


app = FastAPI(title="kurl_api", version=VERSION, lifespan=lifespan)

app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(urls.router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=create_error("Internal server error"),
    )


@app.get("/")
async def root():
    """Service info."""
    return {
        "status": "OK",
        "service": "kurl_api",
        "version": VERSION,
        "uptime_seconds": round(time.time() - started_at, 1),
        "message": "kurl_api is live...",
    }


@app.get("/api")
async def api_root():
    """API info."""
    return {
        "status": "OK",
        "service": "kurl_api",
        "version": VERSION,
        "uptime_seconds": round(time.time() - started_at, 1),
    }


@app.get("/api/healthz")
async def healthz():
    """Liveness check."""
    return {
        "status": "healthy",
        "service": "kurl_api",
        "uptime_seconds": round(time.time() - started_at, 1),
    }
