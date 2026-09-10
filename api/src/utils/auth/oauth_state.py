"""
OAuth State Token
Short-lived, signed state param for a streaming-platform OAuth roundtrip.
An optional subject (user_uid) means link mode; absent means anonymous
sign-in. An optional PKCE verifier can also be carried for providers that
need one back at token exchange.
"""

from utils.auth.jwt_token import sign, verify

_EXPIRY_SECONDS = 600  # 10 minutes -- long enough to complete a consent screen


def create_oauth_state(secret: str, user_uid: str | None = None, verifier: str | None = None) -> str:
    claims = {}
    if user_uid:
        claims["sub"] = user_uid
    if verifier:
        claims["cv"] = verifier
    return sign(claims, secret, _EXPIRY_SECONDS)


def verify_oauth_state(state: str, secret: str) -> tuple[bool, str | None, str | None]:
    """Returns (valid, user_uid, verifier). All optional fields are None
    for a valid anonymous, non-PKCE state, and both are None when invalid."""
    payload = verify(state, secret)
    if payload is None:
        return False, None, None
    return True, payload.get("sub"), payload.get("cv")
