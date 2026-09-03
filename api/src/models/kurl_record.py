"""
Kurl Record Model
Field mapping between DB row and client response for the kurls table.
"""


def to_db_params(
    uid: str,
    user_uid: str,
    source_url: str,
    target_url: str,
    platform: str,
    via: str,
    title: str | None,
    artist: str | None,
) -> tuple:
    return (uid, user_uid, source_url, target_url, platform, via, title, artist)


def from_db_row(row) -> dict:
    return {
        "uid": row["uid"],
        "sourceUrl": row["source_url"],
        "targetUrl": row["target_url"],
        "platform": row["platform"],
        "via": row["via"],
        "title": row["title"],
        "artist": row["artist"],
        "createdAt": row["created_at"],
    }
