"""
Messages Routes
HTTP endpoints for direct messages between friends (signed-in users only).
"""

from api.controllers import messages_controller
from api.middleware.session_auth import require_session
from utils.http.response import parse_json_body, respond

_ERROR_STATUS = {
    "INVALID_REQUEST": 400,
    "EMPTY_MESSAGE": 400,
    "BODY_TOO_LONG": 400,
    "NOT_FRIENDS": 403,
    "NOT_FOUND": 404,
}


async def list_threads(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    return respond(await messages_controller.list_threads(db, user_uid), _ERROR_STATUS)


async def send(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    body = await parse_json_body(request)
    return respond(await messages_controller.send(db, user_uid, body), _ERROR_STATUS, 201)


async def get_thread(db, request, uid: str):
    user_uid, error = require_session(request)
    if error:
        return error
    return respond(await messages_controller.get_thread(db, user_uid, uid), _ERROR_STATUS)


async def mark_read(db, request, uid: str):
    user_uid, error = require_session(request)
    if error:
        return error
    return respond(await messages_controller.mark_read(db, user_uid, uid), _ERROR_STATUS)


async def delete_message(db, request, uid: str):
    user_uid, error = require_session(request)
    if error:
        return error
    return respond(await messages_controller.delete_message(db, user_uid, uid), _ERROR_STATUS)
