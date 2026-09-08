"""
Google Account Queries
SQL statements for the google_accounts table (a linked Google OAuth account).
"""

UPSERT = """
    INSERT INTO google_accounts
        (user_uid, google_user_id, display_name, access_token, refresh_token, expires_at, scope)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_uid) DO UPDATE SET
        google_user_id = excluded.google_user_id,
        display_name = excluded.display_name,
        access_token = excluded.access_token,
        refresh_token = excluded.refresh_token,
        expires_at = excluded.expires_at,
        scope = excluded.scope
"""

GET_BY_USER_UID = """
    SELECT * FROM google_accounts WHERE user_uid = ?
"""

GET_BY_GOOGLE_USER_ID = """
    SELECT * FROM google_accounts WHERE google_user_id = ?
"""

DELETE_BY_USER_UID = """
    DELETE FROM google_accounts WHERE user_uid = ?
"""
