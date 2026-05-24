"""
Event Routes
HTTP endpoints for analytics events.
"""

from urllib.parse import parse_qs, urlparse

from api.controllers import events_controller
from utils.logging import get_logger
from utils.http.response import json_error, json_response, parse_json_body

logger = get_logger()


async def create_event(db, request):
    try:
        data = await parse_json_body(request)
    except Exception as e:
        logger.error("Failed to parse event body: %s", e)
        return json_error("Invalid JSON body.", 400, code="INVALID_REQUEST")

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
        qs = parse_qs(urlparse(str(request.url)).query)
        if "days" in qs:
            days = max(1, min(365, int(qs["days"][0])))
    except (ValueError, IndexError):
        days = 7

    result = await events_controller.get_summary(db, days)
    return json_response({"status": "success", "data": result})
