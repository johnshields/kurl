# kurl app

Flutter app (iOS, Android, Web).

## Setup

```bash
flutter pub get
flutter run
```

## Web

```bash
flutter run -d chrome --web-port 5173
```

## Config

API base URL and API key are set in `lib/app/config.dart`. Release builds hit `https://api.kurl.online`. Debug builds probe `localhost:8787` (pywrangler dev) and fall back to prod if the worker is offline. The API key is injected at build time via `--dart-define=KURL_API_KEY=...`.
