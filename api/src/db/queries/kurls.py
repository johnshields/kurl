"""
Kurl History Queries
SQL statements for the kurls table (a signed-in user's saved kurls).
"""

INSERT = """
    INSERT INTO kurls (uid, user_uid, source_url, target_url, platform, via, title, artist)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

LIST_FOR_USER = """
    SELECT * FROM kurls WHERE user_uid = ? ORDER BY created_at DESC LIMIT 100
"""

DELETE = """
    DELETE FROM kurls WHERE uid = ? AND user_uid = ?
"""
