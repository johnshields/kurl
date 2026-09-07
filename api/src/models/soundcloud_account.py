"""
SoundCloud Account Model
Field mapping between DB row and client response for the
soundcloud_accounts table. Tokens never leave the server -- only identity
fields are exposed.
"""


def to_db_params(
    user_uid: str,
    soundcloud_user_id: str,
    display_name: str | None,
    access_token: str,
    refresh_token: str,
    expires_at: str,
    scope: str | None,
) -> tuple:
    return (user_uid, soundcloud_user_id, display_name, access_token, refresh_token, expires_at, scope)


def public_soundcloud_account(row) -> dict:
    return {
        "connected": True,
        "soundcloudUserId": row["soundcloud_user_id"],
        "displayName": row["display_name"],
    }
