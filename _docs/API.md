# API

## `POST /resolve`

Only endpoint in phase 1.

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
  "title": "Mirrors",
  "artist": "Justin Timberlake",
  "resolved_url": "https://open.spotify.com/track/...",
  "platform": "spotify",
  "cached": false
}
```

**What happens**
1. Check Redis cache (key: `md5(url + platform)`)
2. Miss → hit Odesli
3. Cache with 24h TTL
4. Return
