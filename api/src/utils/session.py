"""
Session tokens
Stateless JWT for user sessions. Phase 1 has no revocation -- logout is
client-side token discard only. Signed with SESSION_SECRET, a dedicated
secret separate from KURL_API_KEY (the admin/API key).
"""

from utils.jwt_token import sign, verify

_EXPIRY_SECONDS = 60 * 60 * 24 * 30  # 30 days


def create_session_token(user_uid: str, secret: str) -> str:
    return sign({"sub": user_uid}, secret, _EXPIRY_SECONDS)


def verify_session_token(token: str, secret: str) -> str | None:
    payload = verify(token, secret)
    return payload.get("sub") if payload else None
