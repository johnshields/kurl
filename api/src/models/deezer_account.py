"""
Deezer Account Model
Field mapping between DB row and client response for the deezer_accounts
table. The access token never leaves the server -- only identity fields
are exposed.
"""


def to_db_params(
    user_uid: str,
    deezer_user_id: str,
    display_name: str | None,
    access_token: str,
    expires_at: str | None,
) -> tuple:
    return (user_uid, deezer_user_id, display_name, access_token, expires_at)


def public_deezer_account(row) -> dict:
    return {
        "connected": True,
        "deezerUserId": row["deezer_user_id"],
        "displayName": row["display_name"],
    }
