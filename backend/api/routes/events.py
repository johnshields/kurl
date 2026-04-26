"""
Event Routes
HTTP endpoints for analytics events.
"""

import json

from api.controllers import events_controller
from utils.logging import get_logger
from utils.response import json_error, json_response

logger = get_logger()


async def create_event(db, request):
    try:
        body = await request.text()
        data = json.loads(body) if body else {}
    except Exception as e:
        logger.error("Failed to parse event body: %s", e)
        return json_error("Invalid JSON body.", 400)

    meta = {
        "referrer": request.headers.get("Referer"),
        "userAgent": request.headers.get("User-Agent"),
        "country": request.headers.get("CF-IPCountry"),
    }

    result = await events_controller.create_event(db, data, meta)
    return json_response(result, 201)


async def get_summary(db, request):
    days = 7
    try:
        url = str(request.url)
        if "days=" in url:
            raw = url.split("days=", 1)[1].split("&")[0]
            days = max(1, min(365, int(raw)))
    except (ValueError, IndexError):
        days = 7

    result = await events_controller.get_summary(db, days)
    return json_response({"status": "success", "data": result})
