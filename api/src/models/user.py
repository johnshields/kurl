"""
User Model
Field mapping between DB row and client response for the users table.
"""


def to_db_params(uid: str, email: str, username: str, password_hash: str) -> tuple:
    return (uid, email, username, password_hash)


def public_user(row) -> dict:
    return {
        "uid": row["uid"],
        "email": row["email"],
        "username": row["username"],
        "preferredPlatform": row["preferred_platform"],
        "createdAt": row["created_at"],
    }
