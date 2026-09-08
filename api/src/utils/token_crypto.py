"""
Token Encryption
AES-256-GCM via crypto.subtle (Pyodide JS FFI).
"""

import base64
import secrets

from app.config import settings
from utils.logging import get_logger

logger = get_logger()

_ALGORITHM = "AES-GCM"
_IV_BYTES = 12


def is_configured() -> bool:
    return bool(settings.TOKEN_ENCRYPTION_KEY)


def _js_crypto():
    from js import Object, crypto
    from pyodide.ffi import to_js

    return crypto, Object, to_js


async def _import_key(crypto, Object, to_js):
    key_bytes = bytes.fromhex(settings.TOKEN_ENCRYPTION_KEY)
    return await crypto.subtle.importKey(
        "raw",
        to_js(key_bytes),
        to_js({"name": _ALGORITHM}, dict_converter=Object.fromEntries),
        False,
        to_js(["encrypt", "decrypt"]),
    )


async def encrypt_token(plaintext: str | None) -> str | None:
    """Returns "<iv_b64>:<ciphertext_b64>", or None if encryption isn't
    possible (no key configured, or the FFI call failed)."""
    if not plaintext or not is_configured():
        return None
    try:
        crypto, Object, to_js = _js_crypto()
        iv = secrets.token_bytes(_IV_BYTES)
        key = await _import_key(crypto, Object, to_js)
        ciphertext = await crypto.subtle.encrypt(
            to_js({"name": _ALGORITHM, "iv": to_js(iv)}, dict_converter=Object.fromEntries),
            key,
            to_js(plaintext.encode()),
        )
        ciphertext_bytes = bytes(ciphertext.to_py())
        return f"{base64.b64encode(iv).decode()}:{base64.b64encode(ciphertext_bytes).decode()}"
    except Exception as e:
        logger.warning("Token encryption failed: %s", e)
        return None


async def decrypt_token(stored: str | None) -> str | None:
    """Inverse of encrypt_token. A token that can't be decrypted is
    treated as absent, never as plaintext."""
    if not stored or not is_configured():
        return None
    try:
        iv_b64, ciphertext_b64 = stored.split(":", 1)
        crypto, Object, to_js = _js_crypto()
        key = await _import_key(crypto, Object, to_js)
        plaintext = await crypto.subtle.decrypt(
            to_js(
                {"name": _ALGORITHM, "iv": to_js(base64.b64decode(iv_b64))},
                dict_converter=Object.fromEntries,
            ),
            key,
            to_js(base64.b64decode(ciphertext_b64)),
        )
        return bytes(plaintext.to_py()).decode()
    except Exception as e:
        logger.warning("Token decryption failed: %s", e)
        return None
