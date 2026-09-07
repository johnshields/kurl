-- Users table
-- Account records for the (optional) kurl account system.
-- email/password_hash are nullable -- an account created via Sign in with
-- Spotify has neither until/unless a password is set separately.

CREATE TABLE IF NOT EXISTS users (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    uid                 TEXT NOT NULL UNIQUE,
    email               TEXT UNIQUE,
    username            TEXT NOT NULL UNIQUE,
    password_hash       TEXT,
    preferred_platform  TEXT,
    email_verified_at   TEXT,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
