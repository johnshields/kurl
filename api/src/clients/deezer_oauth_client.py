"""
Deezer OAuth Client
User-authorised Deezer access (Sign in with Deezer) -- authorization_code
grant. Separate from clients/platforms/deezer.py, which is the public,
credential-free client used for kurl's own catalog lookups.

Deezer's OAuth flow predates the OAuth2 state parameter and does not
reliably return one on redirect. The CSRF/mode token is embedded directly
in the redirect_uri query string instead -- Deezer preserves it since
that URI is simply the destination it redirects to with ?code= appended.
See deezer_auth_controller for where that redirect_uri is built.

The token exchange returns a query string, not JSON. No refresh token is
issued -- an offline_access-scoped token does not expire.
"""

from urllib.parse import parse_qsl, urlencode

from app.constants import DEEZER_API_BASE, DEEZER_AUTHORIZE_URL, DEEZER_TOKEN_URL
from clients._http import get_client

# Identity only -- offline_access requests a non-expiring token; email is
# needed to match/link an existing email/password account by address.
PERMS = "basic_access,email,offline_access"


def build_authorize_url(app_id: str, redirect_uri_with_state: str) -> str:
    params = {"app_id": app_id, "redirect_uri": redirect_uri_with_state, "perms": PERMS}
    return f"{DEEZER_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code(app_id: str, secret: str, code: str) -> dict:
    """Returns {access_token, expires, ...} -- query-string response, not JSON."""
    response = await get_client("deezer_oauth").get(
        DEEZER_TOKEN_URL,
        params={"app_id": app_id, "secret": secret, "code": code},
    )
    response.raise_for_status()
    return dict(parse_qsl(response.text))


async def fetch_profile(access_token: str) -> dict:
    """GET /user/me -- returns the authorised user's Deezer profile."""
    response = await get_client("deezer_oauth").get(
        f"{DEEZER_API_BASE}/user/me",
        params={"access_token": access_token},
    )
    response.raise_for_status()
    return response.json()
