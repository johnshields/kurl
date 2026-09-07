"""
OAuth State Token
Short-lived, signed state param for a streaming-platform OAuth roundtrip.
An optional subject (user_uid) means link mode; absent means anonymous
sign-in. An optional PKCE verifier can also be carried for providers that
need one back at token exchange.
"""

import time

import jwt

_ALGORITHM = "HS256"
_EXPIRY_SECONDS = 600  # 10 minutes -- long enough to complete a consent screen


def create_oauth_state(secret: str, user_uid: str | None = None, verifier: str | None = None) -> str:
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + _EXPIRY_SECONDS,
    }
    if user_uid:
        payload["sub"] = user_uid
    if verifier:
        payload["cv"] = verifier
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def verify_oauth_state(state: str, secret: str) -> tuple[bool, str | None, str | None]:
    """Returns (valid, user_uid, verifier). All optional fields are None
    for a valid anonymous, non-PKCE state, and both are None when invalid."""
    try:
        payload = jwt.decode(state, secret, algorithms=[_ALGORITHM])
    except jwt.PyJWTError:
        return False, None, None
    return True, payload.get("sub"), payload.get("cv")
