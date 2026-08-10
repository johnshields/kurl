# kurl

> Share any song. To anyone. On any streaming service.

Cross-platform music link resolver: a Flutter app and a Python API on Cloudflare Workers. Paste a Spotify/Apple Music/Tidal/etc. link, get back the same track on whatever platform your friend uses, resolved via ISRC/UPC matching with an Odesli fallback.

**[kurl.online](https://kurl.online)**

## Components

- **api**: Cloudflare Workers Python service. Parses the source URL, resolves via ISRC/UPC against the source and target platform APIs (`via=isrc`/`upc`), falls back to a rescue-resolver chain (iTunes, Genius, Last.fm, DuckDuckGo search) for platforms without a native client, then Odesli, then a search-page deep-link (`via=search`). Results cached in KV; every kurl and page view logged to D1 for the `/admin` analytics console.
- **app**: Flutter client (iOS, Android, Web). Share-sheet and universal-link intake, platform picker, result card. Calls `POST /api/kurl`.

All communication between app and api runs over the public HTTP API - see [.assets/API.md](.assets/API.md).

## Resolution logic

Fast path first, cheapest and most confident match wins:

1. KV cache hit
2. Direct ISRC/UPC lookup against source + target platform APIs
3. Rescue-resolver chain (target-specific, see [.assets/ISRC_KURLER.md](.assets/ISRC_KURLER.md))
4. Odesli fallback (by-id or by-url)
5. Search-page deep-link into the target platform

Full breakdown: [.assets/ISRC_KURLER.md](.assets/ISRC_KURLER.md).

## Supported platforms

Spotify, Apple Music, YouTube Music, SoundCloud, Beatport, Bandcamp, Amazon Music, Tidal, Deezer.

## Stack

- **API** - Python on Cloudflare Workers (Pyodide runtime)
- **App** - Flutter (iOS, Android, Web)
- **Cache** - Cloudflare KV
- **Analytics** - Cloudflare D1 (SQLite)
- **CI/CD** - GitHub Actions (lint, deploy, smoke test)

## License

[MIT](LICENSE)
