"""
Message Queries
SQL statements for the messages table (thread messages, text and/or kurl).
"""

INSERT = """
    INSERT INTO messages (uid, thread_uid, sender_uid, body, kurl, kurl_recipient)
    VALUES (?, ?, ?, ?, ?, ?)
"""

GET_BY_UID = """
    SELECT * FROM messages WHERE uid = ?
"""

LIST_FOR_THREAD = """
    SELECT * FROM messages
    WHERE thread_uid = ?
    ORDER BY created_at ASC
    LIMIT 200
"""

DELETE = """
    DELETE FROM messages WHERE uid = ? AND sender_uid = ?
"""
