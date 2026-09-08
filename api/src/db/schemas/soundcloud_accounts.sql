-- SoundCloud accounts table
-- Links a kurl account to a connected SoundCloud account (Sign in with SoundCloud).

CREATE TABLE IF NOT EXISTS soundcloud_accounts (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_uid           TEXT NOT NULL UNIQUE,
    soundcloud_user_id TEXT NOT NULL,
    display_name       TEXT,
    access_token       TEXT NOT NULL,
    refresh_token      TEXT NOT NULL,
    expires_at         TEXT NOT NULL,
    scope              TEXT,
    created_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_uid) REFERENCES users(uid)
);

CREATE INDEX IF NOT EXISTS idx_soundcloud_accounts_user_uid ON soundcloud_accounts(user_uid);
