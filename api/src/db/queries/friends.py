"""
Friend Queries
SQL statements for the friends table (the friend-request graph).
"""

INSERT = """
    INSERT INTO friends (uid, requester_uid, addressee_uid)
    VALUES (?, ?, ?)
"""

GET_BY_UID = """
    SELECT * FROM friends WHERE uid = ?
"""

GET_BETWEEN = """
    SELECT * FROM friends
    WHERE (requester_uid = ? AND addressee_uid = ?)
       OR (requester_uid = ? AND addressee_uid = ?)
"""

ACCEPT = """
    UPDATE friends
    SET status = 'accepted', responded_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE uid = ? AND addressee_uid = ? AND status = 'pending'
"""

DELETE = """
    DELETE FROM friends
    WHERE uid = ? AND (requester_uid = ? OR addressee_uid = ?)
"""

LIST_ACCEPTED = """
    SELECT * FROM friends
    WHERE status = 'accepted' AND (requester_uid = ? OR addressee_uid = ?)
    ORDER BY responded_at DESC
"""

LIST_INCOMING = """
    SELECT * FROM friends
    WHERE addressee_uid = ? AND status = 'pending'
    ORDER BY created_at DESC
"""

LIST_OUTGOING = """
    SELECT * FROM friends
    WHERE requester_uid = ? AND status = 'pending'
    ORDER BY created_at DESC
"""

ARE_FRIENDS = """
    SELECT 1 FROM friends
    WHERE status = 'accepted'
      AND ((requester_uid = ? AND addressee_uid = ?)
        OR (requester_uid = ? AND addressee_uid = ?))
    LIMIT 1
"""
