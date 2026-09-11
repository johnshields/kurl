"""
Auth Routes
HTTP endpoints for signup, login, and the current user. Accounts are
optional -- kurling itself never requires one.
"""

from api.controllers import auth_controller
from api.middleware.session_auth import require_session
from utils.http.response import parse_json_body, respond

_ERROR_STATUS = {
    "INVALID_EMAIL": 400,
    "WEAK_PASSWORD": 400,
    "EMAIL_TAKEN": 409,
    "INVALID_CREDENTIALS": 401,
    "AUTH_REQUIRED": 401,
    "NOT_FOUND": 404,
    "UNKNOWN_PLATFORM": 400,
    "INVALID_USERNAME": 400,
    "USERNAME_TAKEN": 409,
    "INVALID_TOKEN": 400,
}


async def signup(db, request):
    body = await parse_json_body(request)
    result = await auth_controller.signup(db, body)
    return respond(result, _ERROR_STATUS, 201)


async def login(db, request):
    body = await parse_json_body(request)
    result = await auth_controller.login(db, body)
    return respond(result, _ERROR_STATUS)


async def forgot_password(db, request):
    body = await parse_json_body(request)
    result = await auth_controller.forgot_password(db, body)
    return respond(result, _ERROR_STATUS)


async def reset_password(db, request):
    body = await parse_json_body(request)
    result = await auth_controller.reset_password(db, body)
    return respond(result, _ERROR_STATUS)


async def verify_email(db, request):
    body = await parse_json_body(request)
    result = await auth_controller.verify_email(db, body)
    return respond(result, _ERROR_STATUS)


async def resend_verification(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    result = await auth_controller.resend_verification(db, user_uid)
    return respond(result, _ERROR_STATUS)


async def get_profile(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    result = await auth_controller.get_me(db, user_uid)
    return respond(result, _ERROR_STATUS)


async def update_profile(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    body = await parse_json_body(request)
    result = await auth_controller.update_profile(db, user_uid, body)
    return respond(result, _ERROR_STATUS)
