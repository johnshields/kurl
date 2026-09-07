"""
Spotify Account Queries
SQL statements for the spotify_accounts table (a linked Spotify OAuth account).
"""

UPSERT = """
    INSERT INTO spotify_accounts
        (user_uid, spotify_user_id, display_name, access_token, refresh_token, expires_at, scope)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_uid) DO UPDATE SET
        spotify_user_id = excluded.spotify_user_id,
        display_name = excluded.display_name,
        access_token = excluded.access_token,
        refresh_token = excluded.refresh_token,
        expires_at = excluded.expires_at,
        scope = excluded.scope
"""

GET_BY_USER_UID = """
    SELECT * FROM spotify_accounts WHERE user_uid = ?
"""

GET_BY_SPOTIFY_USER_ID = """
    SELECT * FROM spotify_accounts WHERE spotify_user_id = ?
"""

DELETE_BY_USER_UID = """
    DELETE FROM spotify_accounts WHERE user_uid = ?
"""
