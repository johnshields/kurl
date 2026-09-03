"""
Username generation
Random two-word slugs via coolname (pure Python, no deps -- safe for the
Pyodide/Workers runtime). Uniqueness is checked by the caller against the DB.
"""

import secrets

_MAX_LENGTH = 40


def generate_username() -> str:
    # Deferred: coolname's RNG init calls random.randrange() at import time, blocked outside request context.
    from coolname import generate_slug

    return generate_slug(2)[:_MAX_LENGTH]


def generate_username_with_suffix() -> str:
    """For the rare case generate_username() keeps colliding -- adds a short
    random suffix to break the tie."""
    from coolname import generate_slug

    return f"{generate_slug(2)}-{secrets.token_hex(2)}"[:_MAX_LENGTH]


def is_valid_username(username: str) -> bool:
    return 3 <= len(username) <= _MAX_LENGTH and all(
        c.isalnum() or c in "-_" for c in username
    )
