"""
Kurls Routes
HTTP endpoint for a signed-in user's saved kurl history.
"""

from api.controllers import kurls_controller
from api.middleware.session_auth import require_session
from utils.http.response import json_response


async def list_kurls(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    result = await kurls_controller.list_kurls(db, user_uid)
    return json_response(result)
