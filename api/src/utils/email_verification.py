"""
Email Verification Token
Signed token for the "verify your email" link -- stateless, no DB table.
No fingerprint needed like password_reset.py: re-verifying an already
verified account is a harmless no-op, so the token doesn't need to
self-invalidate on use.
"""

from utils.jwt_token import sign, verify

_EXPIRY_SECONDS = 60 * 60 * 24  # 24 hours


def create_verification_token(user_uid: str, secret: str) -> str:
    return sign({"sub": user_uid}, secret, _EXPIRY_SECONDS)


def decode_verification_token(token: str, secret: str) -> str | None:
    payload = verify(token, secret)
    return payload.get("sub") if payload else None
