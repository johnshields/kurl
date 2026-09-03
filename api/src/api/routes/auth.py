"""
Auth Routes
HTTP endpoints for signup, login, and the current user. Accounts are
optional -- kurling itself never requires one.
"""

from api.controllers import auth_controller
from api.middleware.session_auth import require_session
from utils.http.response import json_error, json_response, parse_json_body

_ERROR_STATUS = {
    "INVALID_EMAIL": 400,
    "WEAK_PASSWORD": 400,
    "EMAIL_TAKEN": 409,
    "INVALID_CREDENTIALS": 401,
    "NOT_FOUND": 404,
    "UNKNOWN_PLATFORM": 400,
    "INVALID_USERNAME": 400,
    "USERNAME_TAKEN": 409,
}


def _respond(result: dict, success_status: int = 200):
    if result["status"] == "error":
        return json_error(result["message"], _ERROR_STATUS.get(result["code"], 400), code=result["code"])
    return json_response(result, success_status)


async def signup(db, request):
    body = await parse_json_body(request)
    result = await auth_controller.signup(db, body)
    return _respond(result, 201)


async def login(db, request):
    body = await parse_json_body(request)
    result = await auth_controller.login(db, body)
    return _respond(result)


async def get_profile(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    result = await auth_controller.get_me(db, user_uid)
    return _respond(result)


async def update_profile(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    body = await parse_json_body(request)
    result = await auth_controller.update_profile(db, user_uid, body)
    return _respond(result)
