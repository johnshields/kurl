"""
UID Generator
Prefixed unique identifier generation for D1 rows.
"""

import secrets


def gen_uid(prefix: str) -> str:
    hex_part = secrets.token_hex(3).upper()
    return f"{prefix}_{hex_part}"
