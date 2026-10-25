"""
Username generation
Random music-themed slugs from kurlname, with collision handling for unique usernames.
"""

import secrets

from db.db import fetch_one
from db.queries import users as queries
from utils.kurlname import generate as generate_name

_MAX_LENGTH = 40

# Safety cap so a full username table can't loop signup forever.
_MAX_ATTEMPTS = 10


def generate_username() -> str:
    return generate_name()[:_MAX_LENGTH]


def generate_username_with_suffix() -> str:
    """For the rare case generate_username() keeps colliding -- adds a short
    random suffix to break the tie."""
    return f"{generate_name()}-{secrets.token_hex(2)}"[:_MAX_LENGTH]


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
