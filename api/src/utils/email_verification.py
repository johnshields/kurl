"""
Email Verification Token
Signed token for the "verify your email" link -- stateless, no DB table.
No fingerprint needed like password_reset.py: re-verifying an already
verified account is a harmless no-op, so the token doesn't need to
self-invalidate on use.
"""

import time

import jwt

_ALGORITHM = "HS256"
_EXPIRY_SECONDS = 60 * 60 * 24  # 24 hours


def create_verification_token(user_uid: str, secret: str) -> str:
    payload = {
        "sub": user_uid,
        "iat": int(time.time()),
        "exp": int(time.time()) + _EXPIRY_SECONDS,
    }
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def decode_verification_token(token: str, secret: str) -> str | None:
    try:
        payload = jwt.decode(token, secret, algorithms=[_ALGORITHM])
    except jwt.PyJWTError:
        return None
    return payload.get("sub")
