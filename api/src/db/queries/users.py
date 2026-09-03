"""
User Queries
SQL statements for the users table.
"""

INSERT = """
    INSERT INTO users (uid, email, username, password_hash)
    VALUES (?, ?, ?, ?)
"""

GET_BY_EMAIL = """
    SELECT * FROM users WHERE email = ?
"""

GET_BY_UID = """
    SELECT * FROM users WHERE uid = ?
"""

GET_BY_USERNAME = """
    SELECT * FROM users WHERE username = ?
"""

UPDATE_USERNAME = """
    UPDATE users SET username = ? WHERE uid = ?
"""

UPDATE_PREFERRED_PLATFORM = """
    UPDATE users SET preferred_platform = ? WHERE uid = ?
"""
