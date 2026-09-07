"""
Spotify Auth Routes
HTTP endpoints for linking/unlinking a Spotify account (Sign in with
Spotify). The callback is hit directly by Spotify's browser redirect, so
it carries no session header -- see spotify_auth_controller for how it
authenticates via the state param instead.
"""

from urllib.parse import parse_qs, urlparse

from api.controllers import spotify_auth_controller
from api.middleware.session_auth import get_session_user_uid, require_session
from utils.http.response import json_error, json_response, redirect


async def status(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    account = await spotify_auth_controller.get_linked_account(db, user_uid)
    return json_response({"status": "success", "data": account})


async def start(db, request):
    # No session required -- this doubles as full sign-in for a visitor with
    # no kurl account yet. A valid session (if present) switches it to link
    # mode instead, tying Spotify to that account -- see oauth_state.py.
    user_uid = get_session_user_uid(request)
    url = spotify_auth_controller.build_authorize_url(user_uid)
    if not url:
        return json_error("Spotify sign-in is not configured.", 503, code="SPOTIFY_NOT_CONFIGURED")
    return json_response({"status": "success", "data": {"url": url}})


async def callback(db, request):
    qs = parse_qs(urlparse(str(request.url)).query)
    code = qs.get("code", [None])[0]
    state = qs.get("state", [None])[0]
    error = qs.get("error", [None])[0]
    redirect_url = await spotify_auth_controller.handle_callback(db, code, state, error)
    return redirect(redirect_url)


async def disconnect(db, request):
    user_uid, error = require_session(request)
    if error:
        return error
    await spotify_auth_controller.disconnect(db, user_uid)
    return json_response({"status": "success", "message": "Spotify disconnected."})
