"""
Kurls Routes
HTTP endpoint for a signed-in user's saved kurl history.
"""

from api.controllers import kurls_controller
from api.middleware.session_auth import with_session
from utils.http.response import json_response


@with_session
async def list_kurls(db, request, user_uid):
    result = await kurls_controller.list_kurls(db, user_uid)
    return json_response(result)


@with_session
async def delete_kurl(db, request, user_uid, uid: str):
    result = await kurls_controller.delete_kurl(db, user_uid, uid)
    return json_response(result)
