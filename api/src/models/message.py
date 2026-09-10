"""
Message Model
Field mapping between a messages row and the client response.
"""

import json


def _loads(raw):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def public_message(row) -> dict:
    return {
        "uid": row["uid"],
        "threadUid": row["thread_uid"],
        "senderUid": row["sender_uid"],
        "body": row["body"],
        "kurl": _loads(row["kurl"]),
        "kurlRecipient": _loads(row["kurl_recipient"]),
        "createdAt": row["created_at"],
    }
