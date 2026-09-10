"""
Thread Queries
SQL statements for the threads table (one row per DM user-pair).
"""

INSERT = """
    INSERT INTO threads (uid, user_a_uid, user_b_uid)
    VALUES (?, ?, ?)
"""

GET_BY_UID = """
    SELECT * FROM threads WHERE uid = ?
"""

GET_BY_PAIR = """
    SELECT * FROM threads WHERE user_a_uid = ? AND user_b_uid = ?
"""

LIST_FOR_USER = """
    SELECT * FROM threads
    WHERE user_a_uid = ? OR user_b_uid = ?
    ORDER BY last_message_at DESC
    LIMIT 100
"""

TOUCH = """
    UPDATE threads
    SET last_message_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE uid = ?
"""

MARK_READ_A = """
    UPDATE threads
    SET last_read_a_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE uid = ?
"""

MARK_READ_B = """
    UPDATE threads
    SET last_read_b_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE uid = ?
"""
