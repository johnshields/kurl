"""
Spotify Auth Routes
HTTP endpoints for Sign in with Spotify. Callback is state-authenticated,
not session-gated -- it's Spotify's own redirect.
"""

from api.controllers import spotify_auth_controller as _controller
from api.routes import _oauth

_LABEL = "Spotify"
_NOT_CONFIGURED = "SPOTIFY_NOT_CONFIGURED"


async def status(db, request):
    return await _oauth.status(_controller, db, request)


async def start(db, request):
    return await _oauth.start(_controller, _LABEL, _NOT_CONFIGURED, db, request)


async def callback(db, request):
    return await _oauth.callback(_controller, db, request)


async def disconnect(db, request):
    return await _oauth.disconnect(_controller, _LABEL, db, request)
