"""
Messages Routes
HTTP endpoints for direct messages between friends (signed-in users only).
"""

from api.controllers import messages_controller
from api.middleware.session_auth import with_session
from utils.http.response import parse_json_body, respond

_ERROR_STATUS = {
    "INVALID_REQUEST": 400,
    "EMPTY_MESSAGE": 400,
    "BODY_TOO_LONG": 400,
    "NOT_FRIENDS": 403,
    "NOT_FOUND": 404,
    "ENCRYPTION_UNAVAILABLE": 503,
}


@with_session
async def list_threads(db, request, user_uid):
    return respond(await messages_controller.list_threads(db, user_uid), _ERROR_STATUS)


@with_session
async def send(db, request, user_uid):
    body = await parse_json_body(request)
    return respond(await messages_controller.send(db, user_uid, body), _ERROR_STATUS, 201)


@with_session
async def get_thread(db, request, user_uid, uid: str):
    return respond(await messages_controller.get_thread(db, user_uid, uid), _ERROR_STATUS)


@with_session
async def mark_read(db, request, user_uid, uid: str):
    return respond(await messages_controller.mark_read(db, user_uid, uid), _ERROR_STATUS)


@with_session
async def delete_message(db, request, user_uid, uid: str):
    return respond(await messages_controller.delete_message(db, user_uid, uid), _ERROR_STATUS)
