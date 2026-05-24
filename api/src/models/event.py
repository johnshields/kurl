"""
Event Model
Field mapping between DB row and client response for the events table.
"""


def to_db_params(data: dict, uid: str, meta: dict) -> tuple:
    return (
        uid,
        data.get("type", ""),
        data.get("sourceUrl") or "",
        data.get("platform") or "",
        data.get("via") or "",
        meta.get("referrer") or "",
        meta.get("userAgent") or "",
        meta.get("country") or "",
    )


def from_db_row(row) -> dict:
    return {
        "uid": row["uid"],
        "type": row["type"],
        "sourceUrl": row["source_url"],
        "platform": row["platform"],
        "via": row.get("via") if hasattr(row, "get") else row["via"],
        "referrer": row["referrer"],
        "userAgent": row["user_agent"],
        "country": row["country"],
        "createdAt": row["created_at"],
    }
