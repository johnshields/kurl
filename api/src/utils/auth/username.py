"""
Username generation
Random adjective-noun slugs: the adjective from coolname, the noun from
randomname's music word lists. Falls back to coolname's own animal slugs if
randomname is unavailable, so signup never fails on naming.
Both packages are pure Python, safe for the Pyodide/Workers runtime.
"""

import secrets

from db.db import fetch_one
from db.queries import users as queries
from utils.logging import get_logger

logger = get_logger()

_MAX_LENGTH = 40

# Safety cap so a full username table can't loop signup forever.
_MAX_ATTEMPTS = 10

_MUSIC_NOUNS = ("n/music_instruments", "n/music_theory")


def _slug() -> str:
    # Imported on use: both packages seed their RNG at import, blocked outside request context.
    from coolname import generate, generate_slug

    try:
        import randomname

        return f"{generate(2)[0]}-{randomname.generate(_MUSIC_NOUNS)}"
    except Exception as e:
        logger.warning("Music username generation failed, using coolname: %s", e)
        return generate_slug(2)


def generate_username() -> str:
    return _slug()[:_MAX_LENGTH]


def generate_username_with_suffix() -> str:
    """For the rare case generate_username() keeps colliding -- adds a short
    random suffix to break the tie."""
    return f"{_slug()}-{secrets.token_hex(2)}"[:_MAX_LENGTH]


def is_valid_username(username: str) -> bool:
    return 3 <= len(username) <= _MAX_LENGTH and all(
        c.isalnum() or c in "-_" for c in username
    )


async def unique_username(db) -> str:
    for _ in range(_MAX_ATTEMPTS):
        candidate = generate_username()
        if not await fetch_one(db, queries.GET_BY_USERNAME, candidate):
            return candidate
    # Exhausted retries -- add a short random suffix, still checked once.
    return generate_username_with_suffix()
