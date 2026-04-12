# Development

## Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Needs a `.env`:
```
REDIS_URL=redis://localhost:6379
ODESLI_API_KEY=optional   # free tier works without a key
```

## Mobile

```bash
cd mobile
flutter pub get
flutter run
```

Use a real device for testing the share extension - simulators are flaky with share sheets.

---

## Flutter packages

| Package | What it does |
|---|---|
| `share_handler` | Intercept OS share sheet |
| `sqflite` | On-device SQLite |
| `dio` | HTTP client |
| `riverpod` | State management |
| `go_router` | Navigation |
| `shared_preferences` | Key/value store (platform pref) |
| `url_launcher` | Open share sheet after resolving |
