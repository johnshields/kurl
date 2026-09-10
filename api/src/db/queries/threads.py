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
    SELECT t.uid, t.last_message_at, t.created_at,
           u.uid AS other_uid, u.username AS other_username,
           m.body AS last_body, m.kurl AS last_kurl,
           m.sender_uid AS last_sender_uid, m.created_at AS last_at,
           (SELECT COUNT(*) FROM messages x
            WHERE x.thread_uid = t.uid AND x.sender_uid != ?
              AND x.created_at > COALESCE(
                  CASE WHEN t.user_a_uid = ? THEN t.last_read_a_at ELSE t.last_read_b_at END, '')
           ) AS unread
    FROM threads t
    JOIN users u
      ON u.uid = CASE WHEN t.user_a_uid = ? THEN t.user_b_uid ELSE t.user_a_uid END
    LEFT JOIN messages m
      ON m.uid = (SELECT uid FROM messages WHERE thread_uid = t.uid
                  ORDER BY created_at DESC, id DESC LIMIT 1)
    WHERE t.user_a_uid = ? OR t.user_b_uid = ?
    ORDER BY t.last_message_at DESC
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
