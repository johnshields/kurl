PLATFORMS = {
    "spotify",
    "appleMusic",
    "youtubeMusic",
    "deezer",
    "tidal",
    "amazonMusic",
    "pandora",
}

OPENAPI_TAGS = [
    {"name": "System", "description": "Health checks, API information, and system status"},
    {"name": "URLs", "description": "Cross-platform URL resolution"},
]

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://kurlshare.com",
    "https://www.kurlshare.com",
]

ERROR_MESSAGES = {
    "UNKNOWN_PLATFORM": "Unknown platform",
    "PLATFORM_NOT_FOUND": "No URL found for this track",
    "ODESLI_ERROR": "Odesli API error",
    "INTERNAL_ERROR": "Internal server error",
}
