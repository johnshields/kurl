import hashlib
import json

from fastapi import HTTPException

from app.constants import PLATFORMS
from clients import cache, odesli
from utils.responses import success
from utils.wrap_route import wrap_route


@wrap_route("Resolve")
async def resolve_link(url: str, target_platform: str):
    """Resolve a streaming URL to the target platform via Odesli."""
    if target_platform not in PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown platform: {target_platform}",
        )

    cache_key = hashlib.md5(
        f"{url}{target_platform}".encode()
    ).hexdigest()

    cached = await cache.get(cache_key)
    if cached:
        data = json.loads(cached)
        data["cached"] = True
        return success("Link resolved from cache", data)

    odesli_data = await odesli.resolve(url)

    resolved_url = odesli.extract_link(odesli_data, target_platform)
    if not resolved_url:
        raise HTTPException(
            status_code=404,
            detail=f"No {target_platform} link found for this track",
        )

    title, artist = odesli.extract_metadata(odesli_data)

    result = {
        "title": title,
        "artist": artist,
        "resolved_url": resolved_url,
        "platform": target_platform,
    }

    await cache.set(cache_key, json.dumps(result))

    result["cached"] = False
    return success("Link resolved", result)
