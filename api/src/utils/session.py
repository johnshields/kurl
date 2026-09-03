"""
Session tokens
Stateless JWT for user sessions. Phase 1 has no revocation -- logout is
client-side token discard only. Signed with SESSION_SECRET, a dedicated
secret separate from KURL_API_KEY (the admin/API key).
"""

import time

import jwt

_ALGORITHM = "HS256"
_EXPIRY_SECONDS = 60 * 60 * 24 * 30  # 30 days


def create_session_token(user_uid: str, secret: str) -> str:
    payload = {
        "sub": user_uid,
        "iat": int(time.time()),
        "exp": int(time.time()) + _EXPIRY_SECONDS,
    }
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def verify_session_token(token: str, secret: str) -> str | None:
    try:
        payload = jwt.decode(token, secret, algorithms=[_ALGORITHM])
    except jwt.PyJWTError:
        return None
    return payload.get("sub")
