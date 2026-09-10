# API

Base URL: `https://api.kurl.online`

## Authentication

Protected endpoints require an API key via header:
```
X-API-Key: <key>
```

| Endpoint | Auth |
|---|---|
| `GET /`, `/api`, `/api/info`, `/api/healthz` | Public |
| `POST /api/events` | Public |
| `POST /api/kurl` | Public |
| `GET /api/readyz` | API key |
| `GET /api/events/summary` | API key |
| `GET /api/events/approx-pairs` | API key |
| `/api/friends/*`, `/api/messages/*` | Session (Bearer) |

## `POST /api/kurl`

The main endpoint - kurls a streaming URL to another platform.

**Request**
```json
{
  "url": "https://music.apple.com/ie/album/...",
  "target_platform": "spotify"
}
```

**Response**
```json
{
  "status": "success",
  "message": "Kurled",
  "data": {
    "title": "Delilah (pull me out of this)",
    "artist": "Fred again..",
    "resolved_url": "https://open.spotify.com/track/...",
    "platform": "spotify",
    "cached": false,
    "via": "isrc"
  }
}
```

### `via` values

Indicates which resolution path produced the link. Ordered from highest to lowest confidence:

| `via` | Meaning |
|---|---|
| `isrc` | Direct ISRC match via source + target platform APIs (best) |
| `upc` | Direct UPC match for albums |
| `name` | Artist name match (only for artist URLs) |
| `search_api` | Metadata scraped from source, found on target via its search API |
| `direct` | Odesli returned a direct target URL |
| `search` | No direct match anywhere - `resolved_url` is a deep-link into the target's search page |

### Resolution order

1. **Cache** - KV lookup by `md5(normalised_url + target_platform)`, 24h TTL
2. **Kurler (fast path)** - parse source URL, call source platform's API for ISRC/UPC, search target platform by the same identifier
3. **Odesli by-id or by-URL** - fallback link resolution
4. **Metadata scraping** - oEmbed for YouTube, OG tags for Apple, etc.
5. **Search URL fallback** - deep-link into the target platform's search page
6. **404** - only when no metadata from any source

## `POST /api/events`

Fire-and-forget analytics event. No auth required.

**Request**
```json
{
  "type": "kurl",
  "sourceUrl": "https://open.spotify.com/track/...",
  "platform": "deezer"
}
```

**Event types**: `page_view`, `kurl`, `kurl_success`, `platform_select`, `open_result`

## `GET /api/events/summary`

Analytics summary. Requires API key. Accepts `?days=7` (1-365).

**Response**
```json
{
  "status": "success",
  "data": {
    "days": 7,
    "totals": {"kurl": 42, "page_view": 100},
    "topPlatforms": [{"platform": "spotify", "count": 20}],
    "countries": [{"country": "IE", "count": 15}],
    "recent": [...]
  }
}
```

## `GET /api/events/approx-pairs`

Source URLs that repeatedly missed on a given target platform (approximate near-matches). Requires API key. Accepts `?days=7`.

**Response**
```json
{
  "status": "success",
  "data": {
    "days": 7,
    "since": "2026-07-28T00:00:00Z",
    "pairs": [{"sourceUrl": "https://open.spotify.com/track/...", "platform": "beatport", "misses": 3}]
  }
}
```

## Friends and messages

Direct messages between friends. Requires a session token (`Authorization: Bearer <token>`). Schema and behaviour in [USERS.md](USERS.md).

### `GET /api/friends`

Accepted friends plus pending requests in each direction.

**Response**
```json
{
  "status": "success",
  "data": {
    "friends": [
      {
        "uid": "FRN_...",
        "user": {"uid": "USR_...", "username": "brave-otter"},
        "status": "accepted",
        "createdAt": "2026-09-10T00:00:00.000Z",
        "respondedAt": "2026-09-10T00:01:00.000Z"
      }
    ],
    "incoming": [],
    "outgoing": []
  }
}
```

### `POST /api/friends`

Send a request. Rejects an unknown username, self, an existing request, or an existing friendship.

**Request**
```json
{"username": "brave-otter"}
```

### `POST /api/friends/:uid/accept`

Accept a pending request. Addressee only.

### `DELETE /api/friends/:uid`

Decline, cancel, or unfriend. Scoped to a participant.

### `GET /api/messages`

Thread list, newest first. Each row carries the other participant, a preview of the last message, and the caller's unread count.

**Response**
```json
{
  "status": "success",
  "data": [
    {
      "uid": "THR_...",
      "user": {"uid": "USR_...", "username": "brave-otter"},
      "lastMessageAt": "2026-09-10T00:00:00.000Z",
      "unread": 2,
      "lastMessage": {
        "body": "check this out",
        "kurl": null,
        "senderUid": "USR_...",
        "createdAt": "2026-09-10T00:00:00.000Z"
      }
    }
  ]
}
```

### `GET /api/messages/:threadUid`

Thread history, oldest first. Marks the caller's side read.

**Response**
```json
{
  "status": "success",
  "data": {
    "thread": {
      "uid": "THR_...",
      "user": {"uid": "USR_...", "username": "brave-otter"},
      "lastMessageAt": "2026-09-10T00:00:00.000Z",
      "lastReadAt": "2026-09-10T00:00:00.000Z",
      "createdAt": "2026-09-09T00:00:00.000Z"
    },
    "messages": [
      {
        "uid": "MSG_...",
        "threadUid": "THR_...",
        "senderUid": "USR_...",
        "body": "check this out",
        "kurl": {
          "source_url": "https://open.spotify.com/track/...",
          "resolved_url": "https://open.spotify.com/track/...",
          "platform": "spotify",
          "via": "isrc",
          "title": "Delilah (pull me out of this)",
          "artist": "Fred again.."
        },
        "kurlRecipient": {"target_url": "https://tidal.com/track/...", "platform": "tidal", "via": "isrc"},
        "createdAt": "2026-09-10T00:00:00.000Z"
      }
    ]
  }
}
```

### `POST /api/messages`

Send a message: text, an attached kurl, or both. `toUsername`, `toUid` or `threadUid` picks the recipient; starting a new thread needs an accepted friendship. When the attached kurl's platform differs from the recipient's preferred platform it is re-resolved server-side and the override stored as `kurlRecipient`.

**Request**
```json
{
  "toUsername": "brave-otter",
  "body": "check this out",
  "kurl": {
    "source_url": "https://open.spotify.com/track/...",
    "resolved_url": "https://open.spotify.com/track/...",
    "platform": "spotify",
    "via": "isrc",
    "title": "Delilah (pull me out of this)",
    "artist": "Fred again.."
  }
}
```

### `POST /api/messages/:threadUid/read`

Mark the caller's side read.

### `DELETE /api/messages/:messageUid`

Delete a message, sender only.

## `GET /api/readyz`

Per-client readiness probe. Pings each configured platform client with a 5s timeout. Requires API key.

**Response (200)**
```json
{
  "status": "ready",
  "service": "kurl_api",
  "uptime_seconds": 12.34,
  "checks": {
    "cache":      {"status": "healthy"},
    "spotify":    {"status": "healthy"},
    "appleMusic": {"status": "skipped", "reason": "no credentials"},
    "deezer":     {"status": "healthy"},
    "tidal":      {"status": "healthy"}
  }
}
```

## System endpoints

| Endpoint | Purpose |
|---|---|
| `GET /` | HTML landing page |
| `GET /api` | Service info (name, version, description, uptime) |
| `GET /api/healthz` | Liveness check |
| `GET /api/readyz` | Readiness check (requires API key) |

## Rate limiting

Write endpoints (POST, PATCH, DELETE) are limited to 10 requests per 60 seconds. `/api/events` is exempt.
