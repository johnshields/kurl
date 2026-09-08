"""
Password Reset Token
Short-lived signed token for forgot-password -- stateless, embeds a password_hash fingerprint so it
self-invalidates once the password actually changes.
"""

import hashlib

from utils.jwt_token import sign, verify

_EXPIRY_SECONDS = 1800  # 30 minutes


def _fingerprint(password_hash: str | None) -> str:
    return hashlib.sha256((password_hash or "").encode()).hexdigest()[:16]


def create_reset_token(user_uid: str, password_hash: str | None, secret: str) -> str:
    return sign({"sub": user_uid, "pwd": _fingerprint(password_hash)}, secret, _EXPIRY_SECONDS)


def decode_reset_token(token: str, secret: str) -> tuple[str, str] | None:
    """Returns (user_uid, password_fingerprint) if signature/expiry valid, else None."""
    payload = verify(token, secret)
    if payload is None:
        return None
    sub, pwd = payload.get("sub"), payload.get("pwd")
    if not sub or not pwd:
        return None
    return sub, pwd


def matches_current_password(fingerprint: str, password_hash: str | None) -> bool:
    return fingerprint == _fingerprint(password_hash)
