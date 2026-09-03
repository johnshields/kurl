-- Kurls table
-- A signed-in user's saved kurl history. Anonymous kurls (no account) are
-- never written here -- they only ever hit the analytics events table.

CREATE TABLE IF NOT EXISTS kurls (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    uid          TEXT NOT NULL UNIQUE,
    user_uid     TEXT NOT NULL,
    source_url   TEXT NOT NULL,
    target_url   TEXT NOT NULL,
    platform     TEXT NOT NULL,
    via          TEXT NOT NULL,
    title        TEXT,
    artist       TEXT,
    created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_uid) REFERENCES users(uid)
);

CREATE INDEX IF NOT EXISTS idx_kurls_user_uid ON kurls(user_uid);
CREATE INDEX IF NOT EXISTS idx_kurls_created_at ON kurls(created_at);
