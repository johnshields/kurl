-- Events table
-- First-party analytics events (kurls, page views, etc).
-- Append-only: no update, no soft-delete.

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    uid         TEXT NOT NULL UNIQUE,
    type        TEXT NOT NULL,
    source_url  TEXT,
    platform    TEXT,
    via         TEXT,
    referrer    TEXT,
    user_agent  TEXT,
    country     TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_events_uid ON events(uid);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_platform ON events(platform);
CREATE INDEX IF NOT EXISTS idx_events_via ON events(via);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
