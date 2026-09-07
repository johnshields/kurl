-- Deezer accounts table
-- Links a kurl account to a connected Deezer account (Sign in with Deezer).
-- Identity only -- the access token is stored so a later phase can call
-- the Deezer API as the user, but nothing here uses it for that yet.
-- No refresh_token column: Deezer's OAuth flow issues none (an
-- offline_access-scoped token doesn't expire; expires_at is NULL then).

CREATE TABLE IF NOT EXISTS deezer_accounts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_uid         TEXT NOT NULL UNIQUE,
    deezer_user_id   TEXT NOT NULL,
    display_name     TEXT,
    access_token     TEXT NOT NULL,
    expires_at       TEXT,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_uid) REFERENCES users(uid)
);

CREATE INDEX IF NOT EXISTS idx_deezer_accounts_user_uid ON deezer_accounts(user_uid);
