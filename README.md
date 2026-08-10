# kurl

Cross-platform music link resolver built with Flutter and Python on Cloudflare Workers. Paste a Spotify/Apple Music/Tidal/etc. link and get back the same track on Spotify, Apple Music, YouTube Music, SoundCloud, Beatport, Bandcamp, Amazon Music, Tidal or Deezer, resolved via ISRC/UPC matching with an Odesli fallback.

**[kurl.online](https://kurl.online)**

## Components

- **api**: Cloudflare Workers Python service. Parses the source URL, resolves via ISRC/UPC against the source and target platform APIs (`via=isrc`/`upc`), falls back to a rescue-resolver chain (iTunes, Genius, Last.fm, DuckDuckGo search) for platforms without a native client, then Odesli, then a search-page deep-link (`via=search`). Results cached in KV; every kurl and page view logged to D1 for the `/admin` analytics console.
- **app**: Flutter client (iOS, Android, Web). Share-sheet and universal-link intake, platform picker, result card. Calls `POST /api/kurl`.

All communication between app and api runs over the public HTTP API - see [.assets/API.md](.assets/API.md).

## Resolution Order

Fast path first, cheapest and most confident match wins:

1. KV cache hit
2. Direct ISRC/UPC lookup against source + target platform APIs
3. Rescue-resolver chain (target-specific)
4. Odesli fallback (by-id or by-url)
5. Search-page deep-link into the target platform

Full breakdown: [.assets/ISRC_KURLER.md](.assets/ISRC_KURLER.md).

## Running the Project

### Stack

- Python on Cloudflare Workers (Pyodide runtime), Cloudflare KV + D1
- Flutter (iOS, Android, Web)
- GitHub Actions (lint, deploy, smoke test)

### 1. Run the API

```bash
cd api
pip install uv
uv tool install workers-py
pywrangler dev
```

Serves on `http://localhost:8787`, live reload on file change.

### 2. Run the app

```bash
cd app
flutter pub get
flutter run
```

Debug builds probe `localhost:8787` and fall back to prod if the worker is offline.

## License

[MIT](LICENSE)
