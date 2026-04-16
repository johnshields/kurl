# API

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

1. **Cache** — Redis `md5(normalised_url + target_platform)`, 24h TTL
2. **Kurler (fast path)** — parse source URL, call source platform's API for ISRC/UPC, search target platform by the same identifier. Requires API creds on the target (and ideally source) platform
3. **Metadata search** — if source has no API, scrape metadata (oEmbed for YouTube, `__NEXT_DATA__` for Spotify, OG tags for Apple) and search target via its search API
4. **Odesli by-id or by-URL** — 3× retry with 1s/2s/4s backoff on 429
5. **Search URL fallback** — build a deep-link into the target platform's search page from scraped metadata
6. **404** — only when we have no metadata from any source

## `GET /api/readyz`

Per-client readiness probe. Pings each configured platform client with a 5s timeout.

**Response (200)**
```json
{
  "status": "ready",
  "service": "kurl_api",
  "uptime_seconds": 12.34,
  "checks": {
    "redis":      {"status": "healthy"},
    "spotify":    {"status": "healthy"},
    "appleMusic": {"status": "skipped", "reason": "no credentials"},
    "deezer":     {"status": "healthy"},
    "tidal":      {"status": "healthy"}
  }
}
```

**Status codes**
- `200 ready` — all configured clients reachable
- `503 degraded` — one or more `unhealthy`; response body lists which and why
- Unconfigured clients (no creds set) return `skipped` — does not trigger 503

Use this in CI smoke tests and deployment health probes.

## System endpoints

| Endpoint | Purpose |
|---|---|
| `GET /` | HTML landing page |
| `GET /api` | Service info (name, version, description, uptime) |
| `GET /api/healthz` | Liveness check — is the process up |
| `GET /api/readyz` | Readiness check — are all dependencies reachable |
| `GET /docs` | Dark-themed Swagger UI |
