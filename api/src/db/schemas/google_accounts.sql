-- Google accounts table
-- Links a kurl account to a connected Google account (Sign in with YouTube).
--
-- Google only issues a refresh_token on first consent (or forced
-- re-consent), so refresh_token can stay empty even after a successful link.

CREATE TABLE IF NOT EXISTS google_accounts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_uid         TEXT NOT NULL UNIQUE,
    google_user_id   TEXT NOT NULL,
    display_name     TEXT,
    access_token     TEXT NOT NULL,
    refresh_token    TEXT,
    expires_at       TEXT NOT NULL,
    scope            TEXT,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_uid) REFERENCES users(uid)
);

CREATE INDEX IF NOT EXISTS idx_google_accounts_user_uid ON google_accounts(user_uid);
