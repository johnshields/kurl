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
| `POST /api/kurl` | API key |
| `GET /api/readyz` | API key |
| `GET /api/events/summary` | API key |

## `POST /api/kurl`

The main endpoint — kurls a streaming URL to another platform.

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
| `search` | No direct match anywhere — `resolved_url` is a deep-link into the target's search page |

### Resolution order

1. **Cache** — KV lookup by `md5(normalised_url + target_platform)`, 24h TTL
2. **Kurler (fast path)** — parse source URL, call source platform's API for ISRC/UPC, search target platform by the same identifier
3. **Odesli by-id or by-URL** — fallback link resolution
4. **Metadata scraping** — oEmbed for YouTube, OG tags for Apple, etc.
5. **Search URL fallback** — deep-link into the target platform's search page
6. **404** — only when no metadata from any source

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
