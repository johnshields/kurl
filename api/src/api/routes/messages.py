"""
Messages Routes
HTTP endpoints for direct messages between friends (signed-in users only).
"""

from api.controllers import messages_controller
from api.middleware.session_auth import require_session
from utils.http.response import json_error, json_response, parse_json_body

_ERROR_STATUS = {
    "INVALID_REQUEST": 400,
    "EMPTY_MESSAGE": 400,
    "BODY_TOO_LONG": 400,
    "NOT_FRIENDS": 403,
    "NOT_FOUND": 404,
}


def _respond(result: dict, success_status: int = 200):
    if result["status"] == "error":
        return json_error(result["message"], _ERROR_STATUS.get(result["code"], 400), code=result["code"])
    return json_response(result, success_status)


async def list_threads(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    return _respond(await messages_controller.list_threads(db, user_uid))


async def send(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    body = await parse_json_body(request)
    return _respond(await messages_controller.send(db, user_uid, body), 201)


async def get_thread(db, request, uid: str):
    user_uid, error = require_session(request)
    if error:
        return error
    return _respond(await messages_controller.get_thread(db, user_uid, uid))


async def mark_read(db, request, uid: str):
    user_uid, error = require_session(request)
    if error:
        return error
    return _respond(await messages_controller.mark_read(db, user_uid, uid))


async def delete_message(db, request, uid: str):
    user_uid, error = require_session(request)
    if error:
        return error
    return _respond(await messages_controller.delete_message(db, user_uid, uid))
