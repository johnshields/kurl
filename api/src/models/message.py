"""
Message Model
Field mapping between a messages row and the client response.
"""

import json


def loads(raw):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def to_db_params(uid, thread_uid, sender_uid, body, kurl, kurl_recipient) -> tuple:
    return (
        uid,
        thread_uid,
        sender_uid,
        body,
        json.dumps(kurl) if kurl is not None else None,
        json.dumps(kurl_recipient) if kurl_recipient is not None else None,
    )


def public_message(row) -> dict:
    return {
        "uid": row["uid"],
        "threadUid": row["thread_uid"],
        "senderUid": row["sender_uid"],
        "body": row["body"],
        "kurl": loads(row["kurl"]),
        "kurlRecipient": loads(row["kurl_recipient"]),
        "createdAt": row["created_at"],
    }
