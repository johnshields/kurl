"""
Friends Routes
HTTP endpoints for the friend-request graph (signed-in users only).
"""

from api.controllers import friends_controller
from api.middleware.session_auth import require_session
from utils.http.response import parse_json_body, respond

_ERROR_STATUS = {
    "INVALID_REQUEST": 400,
    "NOT_FOUND": 404,
    "ALREADY_FRIENDS": 409,
    "REQUEST_EXISTS": 409,
}


async def list_friends(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    return respond(await friends_controller.list_friends(db, user_uid), _ERROR_STATUS)


async def send_request(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    body = await parse_json_body(request)
    return respond(await friends_controller.send_request(db, user_uid, body), _ERROR_STATUS, 201)


async def accept_request(db, request, uid: str):
    user_uid, error = require_session(request)
    if error:
        return error
    return respond(await friends_controller.accept_request(db, user_uid, uid), _ERROR_STATUS)


async def remove(db, request, uid: str):
    user_uid, error = require_session(request)
    if error:
        return error
    return respond(await friends_controller.remove(db, user_uid, uid), _ERROR_STATUS)
