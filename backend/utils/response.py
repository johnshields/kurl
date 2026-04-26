"""
Response Helpers
Shared JSON response builder and request parsing for Workers.
"""

import json
from urllib.parse import urlparse

from workers import Response

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Credentials": "true",
}


def json_response(data: dict, status: int = 200) -> Response:
    return Response(
        json.dumps(data),
        status=status,
        headers={"Content-Type": "application/json", **CORS_HEADERS},
    )


def json_error(message: str, status: int) -> Response:
    return json_response({"status": "error", "message": message}, status)


def json_success(message: str, data: dict) -> Response:
    return json_response({"status": "success", "message": message, "data": data})


def html_response(body: str, status: int = 200) -> Response:
    return Response(
        body,
        status=status,
        headers={"Content-Type": "text/html; charset=utf-8", **CORS_HEADERS},
    )


def preflight() -> Response:
    return Response("", status=204, headers=CORS_HEADERS)


def parse_path(url: str) -> str:
    return urlparse(url).path.rstrip("/") or "/"


async def parse_json_body(request) -> dict:
    text = await request.text()
    return json.loads(text) if text else {}
