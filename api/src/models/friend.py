"""
Friend Model
Field mapping between a friends-join row and the client response.
"""


def public_friend(row) -> dict:
    return {
        "uid": row["uid"],
        "user": {"uid": row["other_uid"], "username": row["other_username"]},
        "status": row["status"],
        "createdAt": row["created_at"],
        "respondedAt": row["responded_at"],
    }
