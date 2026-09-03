"""
Password hashing
PBKDF2-HMAC-SHA256, stdlib only -- no bcrypt/argon2 wheel available in the
Pyodide/Workers runtime. Iteration count is kept well below OWASP's current
600k recommendation deliberately: this runs inside a Worker's CPU-time
budget, not a normal server process -- needs benchmarking against real
Workers CPU limits once local dev is unblocked, see .assets/USERS.md.
"""

import hashlib
import hmac
import secrets

_ITERATIONS = 120_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_hex(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest_hex = stored.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)
