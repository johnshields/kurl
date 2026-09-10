"""
Google Auth Routes
HTTP endpoints for Sign in with YouTube. Callback is state-authenticated,
not session-gated -- it's Google's own redirect.
"""

from api.controllers.oauth import google_auth_controller as _controller
from api.routes import _oauth

_LABEL = "YouTube"
_NOT_CONFIGURED = "GOOGLE_NOT_CONFIGURED"


async def status(db, request):
    return await _oauth.status(_controller, db, request)


async def start(db, request):
    return await _oauth.start(_controller, _LABEL, _NOT_CONFIGURED, db, request)


async def callback(db, request):
    return await _oauth.callback(_controller, db, request)


async def disconnect(db, request):
    return await _oauth.disconnect(_controller, _LABEL, db, request)
