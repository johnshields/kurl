"""
JWT Tokens
Shared HS256 sign/verify for the app's stateless tokens (sessions, OAuth
state, password-reset and email-verification links).
"""

import time

import jwt

_ALGORITHM = "HS256"


def sign(claims: dict, secret: str, ttl_seconds: int) -> str:
    issued_at = int(time.time())
    payload = {**claims, "iat": issued_at, "exp": issued_at + ttl_seconds}
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def verify(token: str, secret: str) -> dict | None:
    try:
        return jwt.decode(token, secret, algorithms=[_ALGORITHM])
    except jwt.PyJWTError:
        return None
