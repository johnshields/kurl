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
    "title": "Mirrors",
    "artist": "Justin Timberlake",
    "resolved_url": "https://open.spotify.com/track/...",
    "platform": "spotify",
    "cached": false,
    "via": "direct"
  }
}
```

`via` is `"direct"` when Odesli returned a direct match, or `"search"` when we fell back to a target-platform search URL (happens on Odesli 429 or when Odesli can't map the track).

**What happens**
1. Check Redis cache (key: `md5(normalised_url + platform)`)
2. Miss → parse source URL, call Odesli by platform + track id (retries up to 3x on 429)
3. If Odesli has no target link → scrape source URL for title + artist and build a search URL
4. Cache with 24h TTL
5. Return

## System endpoints

- `GET /` — HTML landing page with links to `/docs` and `/api`
- `GET /api` — JSON service info (name, version, description, uptime)
- `GET /api/healthz` — liveness check
- `GET /docs` — dark-themed Swagger UI
