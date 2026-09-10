-- Messages table
-- One row per thread message: text (body), an attached kurl, or both.
-- kurl / kurl_recipient are JSON -- the sender's resolved result and the
-- same track re-resolved for the recipient's preferred platform.

CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    uid             TEXT NOT NULL UNIQUE,
    thread_uid      TEXT NOT NULL,
    sender_uid      TEXT NOT NULL,
    body            TEXT,
    kurl            TEXT,
    kurl_recipient  TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (thread_uid) REFERENCES threads(uid),
    FOREIGN KEY (sender_uid) REFERENCES users(uid),
    CHECK (body IS NOT NULL OR kurl IS NOT NULL),
    CHECK (kurl IS NULL OR json_valid(kurl)),
    CHECK (kurl_recipient IS NULL OR json_valid(kurl_recipient))
);

CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_uid, created_at);
