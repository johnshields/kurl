"""
Google Auth Routes
HTTP endpoints for Sign in with YouTube. Callback is state-authenticated,
not session-gated -- it's Google's own redirect.
"""

from urllib.parse import parse_qs, urlparse

from api.controllers import google_auth_controller
from api.middleware.session_auth import get_session_user_uid, require_session
from utils.http.response import json_error, json_response, redirect


async def status(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    account = await google_auth_controller.get_linked_account(db, user_uid)
    return json_response({"status": "success", "data": account})


async def start(db, request):
    # No session required -- full sign-in when absent, link mode when present.
    user_uid = get_session_user_uid(request)
    url = google_auth_controller.build_authorize_url(user_uid)
    if not url:
        return json_error("YouTube sign-in is not configured.", 503, code="GOOGLE_NOT_CONFIGURED")
    return json_response({"status": "success", "data": {"url": url}})


async def callback(db, request):
    qs = parse_qs(urlparse(str(request.url)).query)
    code = qs.get("code", [None])[0]
    state = qs.get("state", [None])[0]
    error = qs.get("error", [None])[0]
    redirect_url = await google_auth_controller.handle_callback(db, code, state, error)
    return redirect(redirect_url)


async def disconnect(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    await google_auth_controller.disconnect(db, user_uid)
    return json_response({"status": "success", "message": "YouTube disconnected."})
