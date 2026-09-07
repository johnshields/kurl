"""
SoundCloud Account Queries
SQL statements for the soundcloud_accounts table (a linked SoundCloud
OAuth account).
"""

UPSERT = """
    INSERT INTO soundcloud_accounts
        (user_uid, soundcloud_user_id, display_name, access_token, refresh_token, expires_at, scope)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_uid) DO UPDATE SET
        soundcloud_user_id = excluded.soundcloud_user_id,
        display_name = excluded.display_name,
        access_token = excluded.access_token,
        refresh_token = excluded.refresh_token,
        expires_at = excluded.expires_at,
        scope = excluded.scope
"""

GET_BY_USER_UID = """
    SELECT * FROM soundcloud_accounts WHERE user_uid = ?
"""

GET_BY_SOUNDCLOUD_USER_ID = """
    SELECT * FROM soundcloud_accounts WHERE soundcloud_user_id = ?
"""

DELETE_BY_USER_UID = """
    DELETE FROM soundcloud_accounts WHERE user_uid = ?
"""
