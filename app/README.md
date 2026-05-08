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

API base URL and API key are set in `lib/app/config.dart`. Release builds hit `https://api.kurl.online`, debug builds hit `localhost:8000`. The API key is injected at build time via `--dart-define`.

## AdSense (web)

Two non-intrusive ad slots: inline (after result card) and footer.

1. Replace `ca-pub-XXXXXXXXXXXXXXXX` in `web/index.html` with your AdSense publisher ID.
2. Pass slot IDs at build time:

```bash
flutter build web --release \
  --dart-define=KURL_API_KEY=<key> \
  --dart-define=ADSENSE_CLIENT=ca-pub-XXXXXXXXXXXXXXXX \
  --dart-define=ADSENSE_SLOT_INLINE=1234567890 \
  --dart-define=ADSENSE_SLOT_FOOTER=0987654321
```

Empty slot env vars hide the corresponding banner — useful for dev builds.
