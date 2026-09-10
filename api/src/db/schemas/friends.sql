-- Friends table
-- Friend-request graph for direct messaging. One row per pair (either
-- direction), status pending -> accepted.

CREATE TABLE IF NOT EXISTS friends (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    uid            TEXT NOT NULL UNIQUE,
    requester_uid  TEXT NOT NULL,
    addressee_uid  TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending',
    created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    responded_at   TEXT,
    FOREIGN KEY (requester_uid) REFERENCES users(uid),
    FOREIGN KEY (addressee_uid) REFERENCES users(uid)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_friends_pair ON friends(requester_uid, addressee_uid);
CREATE INDEX IF NOT EXISTS idx_friends_addressee ON friends(addressee_uid);
