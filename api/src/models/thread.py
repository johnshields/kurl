"""
Thread Model
Field mapping for the threads list row and for a single thread's header.
"""

from models.message import loads


def thread_summary(row) -> dict:
    return {
        "uid": row["uid"],
        "user": {"uid": row["other_uid"], "username": row["other_username"]},
        "lastMessageAt": row["last_message_at"],
        "unread": row["unread"] or 0,
        "lastMessage": _preview(row),
    }


def _preview(row) -> dict | None:
    if not row["last_at"]:
        return None
    return {
        "body": row["last_body"],
        "kurl": loads(row["last_kurl"]),
        "senderUid": row["last_sender_uid"],
        "createdAt": row["last_at"],
    }


def thread_header(row, other: dict, viewer_uid: str) -> dict:
    last_read = row["last_read_a_at"] if row["user_a_uid"] == viewer_uid else row["last_read_b_at"]
    return {
        "uid": row["uid"],
        "user": {"uid": other["uid"], "username": other["username"]},
        "lastMessageAt": row["last_message_at"],
        "lastReadAt": last_read,
        "createdAt": row["created_at"],
    }
