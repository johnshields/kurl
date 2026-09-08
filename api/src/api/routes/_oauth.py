"""
OAuth Auth Routes (shared)
HTTP endpoints common to every streaming-platform sign-in.
"""

from urllib.parse import parse_qs, urlparse

from api.middleware.session_auth import get_session_user_uid, require_session
from utils.http.response import json_error, json_response, redirect


async def status(controller, db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    account = await controller.get_linked_account(db, user_uid)
    return json_response({"status": "success", "data": account})


async def start(controller, label, code, db, request):
    # No session required -- full sign-in when absent, link mode when present.
    user_uid = get_session_user_uid(request)
    url = controller.build_authorize_url(user_uid)
    if not url:
        return json_error(f"{label} sign-in is not configured.", 503, code=code)
    return json_response({"status": "success", "data": {"url": url}})


async def callback(controller, db, request):
    qs = parse_qs(urlparse(str(request.url)).query)
    redirect_url = await controller.handle_callback(
        db, qs.get("code", [None])[0], qs.get("state", [None])[0], qs.get("error", [None])[0]
    )
    return redirect(redirect_url)


async def disconnect(controller, label, db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    await controller.disconnect(db, user_uid)
    return json_response({"status": "success", "message": f"{label} disconnected."})
