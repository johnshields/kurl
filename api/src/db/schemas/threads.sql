-- Threads table
-- One row per DM user-pair, stored sorted (user_a_uid < user_b_uid).
-- last_message_at orders the thread list; last_read_*_at is each side's
-- read pointer (unread = messages newer than the pointer).

CREATE TABLE IF NOT EXISTS threads (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    uid              TEXT NOT NULL UNIQUE,
    user_a_uid       TEXT NOT NULL,
    user_b_uid       TEXT NOT NULL,
    last_message_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    last_read_a_at   TEXT,
    last_read_b_at   TEXT,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_a_uid) REFERENCES users(uid),
    FOREIGN KEY (user_b_uid) REFERENCES users(uid)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_threads_pair ON threads(user_a_uid, user_b_uid);
CREATE INDEX IF NOT EXISTS idx_threads_user_b ON threads(user_b_uid);
CREATE INDEX IF NOT EXISTS idx_threads_last_message_at ON threads(last_message_at);
