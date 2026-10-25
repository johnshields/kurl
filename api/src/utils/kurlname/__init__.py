"""
kurlname
Adjective-noun names with a music noun, e.g. daring-bassoon. The adjective comes from coolname,
the noun from faker-music's instrument and genre lists. Pure Python, no data files. Falls back to
coolname's own slug if faker-music can't load, so naming never breaks signup.
"""

import functools
import re
import secrets
import unicodedata

from utils.logging import get_logger

logger = get_logger()

_MIN_LENGTH, _MAX_LENGTH = 3, 12

# Entries in faker-music that are not music words (names, places, food, abbreviations).
_STOPLIST = frozenset("ccm leona marfa raison raj sambal".split())


def _fold(word: str) -> str:
    return unicodedata.normalize("NFKD", word.strip()).encode("ascii", "ignore").decode().lower()


def _usable(word: str) -> bool:
    return re.fullmatch(r"[a-z]+", word) is not None and _MIN_LENGTH <= len(word) <= _MAX_LENGTH and word not in _STOPLIST


@functools.lru_cache(maxsize=1)
def _nouns() -> tuple[str, ...]:
    try:
        from faker_music.genres import genre_list
        from faker_music.instruments import instrument_list
    except Exception as e:
        logger.warning("faker-music unavailable, using coolname only: %s", e)
        return ()

    words = [w for entry in instrument_list for w in entry["instruments"]]
    for entry in genre_list:
        words.append(entry["genre"])
        words.extend(entry["subgenres"])
    return tuple(sorted(w for w in {_fold(w) for w in words} if _usable(w)))


def generate() -> str:
    # Deferred: coolname's RNG init calls random.randrange() at import time, blocked outside request context.
    from coolname import generate as coolname_words
    from coolname import generate_slug

    nouns = _nouns()
    if not nouns:
        return generate_slug(2)
    return f"{coolname_words(2)[0]}-{secrets.choice(nouns)}"
