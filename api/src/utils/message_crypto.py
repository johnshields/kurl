"""
Message Encryption
AES-256-GCM via crypto.subtle (Pyodide JS FFI), for message bodies at rest.
"""

import base64
import binascii
import secrets

from app.config import settings
from utils.logging import get_logger

logger = get_logger()

_ALGORITHM = "AES-GCM"
_IV_BYTES = 12


class MessageCryptoError(Exception):
    """Encryption or decryption failed."""


def is_configured() -> bool:
    return bool(settings.MESSAGE_ENCRYPTION_KEY)


def _js_crypto():
    from js import Object, crypto
    from pyodide.ffi import to_js

    return crypto, Object, to_js


async def _import_key(crypto, Object, to_js):
    key_bytes = bytes.fromhex(settings.MESSAGE_ENCRYPTION_KEY)
    return await crypto.subtle.importKey(
        "raw",
        to_js(key_bytes),
        to_js({"name": _ALGORITHM}, dict_converter=Object.fromEntries),
        False,
        to_js(["encrypt", "decrypt"]),
    )


def _looks_encrypted(stored: str) -> bool:
    """"<iv_b64>:<ciphertext_b64>" shape, both halves strict base64."""
    parts = stored.split(":", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return False
    try:
        base64.b64decode(parts[0], validate=True)
        base64.b64decode(parts[1], validate=True)
        return True
    except (binascii.Error, ValueError):
        return False


async def encrypt_body(plaintext: str) -> str:
    """Returns "<iv_b64>:<ciphertext_b64>". Raises MessageCryptoError on failure."""
    if not is_configured():
        raise MessageCryptoError("MESSAGE_ENCRYPTION_KEY not configured")
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
        logger.error("Message encryption failed: %s", e)
        raise MessageCryptoError(str(e)) from e


async def decrypt_body(stored: str | None) -> str | None:
    """Inverse of encrypt_body. Plain text passes through unchanged."""
    if not stored or not _looks_encrypted(stored):
        return stored
    if not is_configured():
        raise MessageCryptoError("MESSAGE_ENCRYPTION_KEY not configured")
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
        logger.error("Message decryption failed: %s", e)
        raise MessageCryptoError(str(e)) from e
