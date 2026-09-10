"""
Friend Queries
SQL statements for the friends table (the friend-request graph). The LIST_*
statements join users to carry the other party's uid and username.
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

ARE_FRIENDS = """
    SELECT 1 FROM friends
    WHERE status = 'accepted'
      AND ((requester_uid = ? AND addressee_uid = ?)
        OR (requester_uid = ? AND addressee_uid = ?))
    LIMIT 1
"""

LIST_ACCEPTED = """
    SELECT f.uid, f.status, f.created_at, f.responded_at,
           u.uid AS other_uid, u.username AS other_username
    FROM friends f
    JOIN users u
      ON u.uid = CASE WHEN f.requester_uid = ? THEN f.addressee_uid ELSE f.requester_uid END
    WHERE f.status = 'accepted' AND (f.requester_uid = ? OR f.addressee_uid = ?)
    ORDER BY f.responded_at DESC
"""

LIST_INCOMING = """
    SELECT f.uid, f.status, f.created_at, f.responded_at,
           u.uid AS other_uid, u.username AS other_username
    FROM friends f
    JOIN users u ON u.uid = f.requester_uid
    WHERE f.addressee_uid = ? AND f.status = 'pending'
    ORDER BY f.created_at DESC
"""

LIST_OUTGOING = """
    SELECT f.uid, f.status, f.created_at, f.responded_at,
           u.uid AS other_uid, u.username AS other_username
    FROM friends f
    JOIN users u ON u.uid = f.addressee_uid
    WHERE f.requester_uid = ? AND f.status = 'pending'
    ORDER BY f.created_at DESC
"""
