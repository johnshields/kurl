"""
Streaming Account Model
Field mapping between DB row and client response for the per-provider
linked-account tables. Tokens never leave the server -- only identity
fields are exposed.
"""


def to_db_params(
    user_uid: str,
    provider_user_id: str,
    display_name: str | None,
    access_token: str,
    refresh_token: str,
    expires_at: str,
    scope: str | None,
) -> tuple:
    return (user_uid, provider_user_id, display_name, access_token, refresh_token, expires_at, scope)


def public_account(row, id_column: str, id_key: str) -> dict:
    return {
        "connected": True,
        id_key: row[id_column],
        "displayName": row["display_name"],
    }
