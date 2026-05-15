# kurl api

Cloudflare Workers Python service. Source under `src/`. Deployed via `pywrangler`.

## Setup

```bash
pip install uv
uv tool install workers-py
```

## Run locally

```bash
pywrangler dev
```

Serves on `http://localhost:8787`. Live reload on file change.

## Deploy

```bash
pywrangler deploy
```

## .env

```
ODESLI_API_KEY=
CACHE_TTL_SECONDS=86400

SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
APPLE_TEAM_ID=
APPLE_KEY_ID=
APPLE_PRIVATE_KEY=
TIDAL_CLIENT_ID=
TIDAL_CLIENT_SECRET=
YOUTUBE_API_KEY=
SOUNDCLOUD_CLIENT_ID=
SOUNDCLOUD_CLIENT_SECRET=
```

Production secrets are set via `wrangler secret put`.
