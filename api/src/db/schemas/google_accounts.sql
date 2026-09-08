-- Google accounts table
-- Links a kurl account to a connected Google account (Sign in with
-- YouTube). Identity only -- the tokens are stored so a later phase can
-- call the YouTube API as the user, but nothing here uses them for that
-- yet.
--
-- Google only returns a refresh_token on the first consent for a given
-- user/client pair (or when re-consent is forced) -- expires_at is
-- recomputed on every relink either way, but refresh_token may stay empty.

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
