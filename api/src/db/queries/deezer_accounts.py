"""
Deezer Account Queries
SQL statements for the deezer_accounts table (a linked Deezer OAuth account).
"""

UPSERT = """
    INSERT INTO deezer_accounts
        (user_uid, deezer_user_id, display_name, access_token, expires_at)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(user_uid) DO UPDATE SET
        deezer_user_id = excluded.deezer_user_id,
        display_name = excluded.display_name,
        access_token = excluded.access_token,
        expires_at = excluded.expires_at
"""

GET_BY_USER_UID = """
    SELECT * FROM deezer_accounts WHERE user_uid = ?
"""

GET_BY_DEEZER_USER_ID = """
    SELECT * FROM deezer_accounts WHERE deezer_user_id = ?
"""

DELETE_BY_USER_UID = """
    DELETE FROM deezer_accounts WHERE user_uid = ?
"""
