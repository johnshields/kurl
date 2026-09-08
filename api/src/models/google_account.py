"""
Google Account Model
Field mapping between DB row and client response for the google_accounts
table. Tokens never leave the server -- only identity fields are exposed.
"""


def to_db_params(
    user_uid: str,
    google_user_id: str,
    display_name: str | None,
    access_token: str,
    refresh_token: str,
    expires_at: str,
    scope: str | None,
) -> tuple:
    return (user_uid, google_user_id, display_name, access_token, refresh_token, expires_at, scope)


def public_google_account(row) -> dict:
    return {
        "connected": True,
        "googleUserId": row["google_user_id"],
        "displayName": row["display_name"],
    }
