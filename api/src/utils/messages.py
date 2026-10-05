from urllib.parse import urlparse

ALLOWED_KURL_SCHEMES = ("http", "https")


def has_allowed_scheme(url) -> bool:
    if not isinstance(url, str) or not url:
        return False
    try:
        return urlparse(url).scheme in ALLOWED_KURL_SCHEMES
    except ValueError:
        return False


def pair(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a < b else (b, a)


def is_user_a(row: dict, viewer_uid: str) -> bool:
    return row["user_a_uid"] == viewer_uid


def is_participant(row: dict, viewer_uid: str) -> bool:
    return viewer_uid in (row["user_a_uid"], row["user_b_uid"])


def other_participant(row: dict, viewer_uid: str) -> str:
    return row["user_b_uid"] if is_user_a(row, viewer_uid) else row["user_a_uid"]
