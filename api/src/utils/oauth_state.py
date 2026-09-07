"""
OAuth State Token
Short-lived, signed state param for a Spotify OAuth roundtrip -- separate
from session.py's 30-day session tokens. An optional subject (user_uid)
present means link mode; absent means anonymous sign-in.
"""

import time

import jwt

_ALGORITHM = "HS256"
_EXPIRY_SECONDS = 600  # 10 minutes -- long enough to complete Spotify's consent screen


def create_oauth_state(secret: str, user_uid: str | None = None) -> str:
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + _EXPIRY_SECONDS,
    }
    if user_uid:
        payload["sub"] = user_uid
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def verify_oauth_state(state: str, secret: str) -> tuple[bool, str | None]:
    """Returns (valid, user_uid). user_uid is None for a valid anonymous
    sign-in state, and always None when valid is False."""
    try:
        payload = jwt.decode(state, secret, algorithms=[_ALGORITHM])
    except jwt.PyJWTError:
        return False, None
    return True, payload.get("sub")
