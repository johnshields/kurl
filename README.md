# kurl

> Share any song. To anyone. On any streaming service.

kurl intercepts music share links and converts them to whatever streaming service your friend actually uses.

## Stack

- **API** - Python on Cloudflare Workers (Pyodide runtime)
- **App** - Flutter (iOS, Android, Web)
- **Cache** - Cloudflare KV
- **Analytics** - Cloudflare D1 (SQLite)
- **CI/CD** - GitHub Actions (lint, deploy, smoke test)

## Supported platforms

Spotify, Apple Music, YouTube Music, SoundCloud, Beatport, Bandcamp, Amazon Music, Tidal, Deezer.
