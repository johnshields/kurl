# kurl

> Share any song. To anyone. On any streaming service.

kurl intercepts music share links and converts them to whatever streaming service your friend actually uses.

## Stack

- **Backend** — Python on Cloudflare Workers (Pyodide runtime)
- **Frontend** — Flutter (iOS, Android, Web)
- **Cache** — Cloudflare KV
- **Analytics** — Cloudflare D1 (SQLite)
- **CI/CD** — GitHub Actions (lint, deploy, smoke test)

## Supported platforms

Spotify, Apple Music, YouTube Music, Deezer, Tidal, SoundCloud, Amazon Music, Audiomack, Pandora.

## Docs

See [`_docs/`](_docs/) for architecture, API reference, CI, and development setup.
