# Development

## Backend (Python / FastAPI)

### Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment
Create a `.env` in `backend/`:
```bash
# Core
REDIS_URL=redis://localhost:6379
ODESLI_API_KEY=              # optional — free tier works without
CACHE_TTL_SECONDS=86400

# Spotify — https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=

# Apple Music — needs paid Developer Program enrolment
APPLE_TEAM_ID=
APPLE_KEY_ID=
APPLE_PRIVATE_KEY=           # paste full .p8 PEM contents

# Tidal — https://developer.tidal.com/dashboard
TIDAL_CLIENT_ID=
TIDAL_CLIENT_SECRET=
```
Deezer needs nothing (public API).

### Run
```bash
uvicorn main:app --reload
```

Hit `http://localhost:8000/api/readyz` to see which clients are live.

### Tests
```bash
pytest                   # full suite (94 tests)
pytest __tests__/unit/   # unit only
pytest -v -k youtube     # match by keyword
pytest --cov             # coverage report
```

### Linting
```bash
ruff check .             # lint
ruff format .            # autoformat
ruff format --check .    # check only (what CI runs)
```

Ruff config in `backend/ruff.toml`. Rules: `E` (pycodestyle), `F` (pyflakes), `I` (isort), `B` (bugbear), `UP` (pyupgrade). Line length 120.

## Mobile (Flutter)

```bash
cd app
flutter pub get
flutter run
```

Use a real device for testing the share extension — simulators are flaky with share sheets.

### Key packages

| Package | Purpose |
|---|---|
| `share_handler` | Intercept OS share sheet |
| `sqflite` | On-device SQLite |
| `dio` | HTTP client |
| `riverpod` | State management |
| `go_router` | Navigation |
| `shared_preferences` | Key/value store (platform pref) |
| `url_launcher` | Open share sheet after resolving |
| `simple_icons` | Platform brand icons |

## CI

Pipeline is `.github/workflows/kurl.yml`. Three jobs chained via `needs:`:

1. **lint** — `ruff check` + `ruff format --check` (fast fail)
2. **test** — matrix over Python 3.11 and 3.12, pytest with coverage, codecov upload
3. **smoke** — boots uvicorn, hits `/api/healthz` then `/api/readyz` with real platform creds from the `kurl_env` environment

Secrets live on the `kurl_env` GitHub environment. Add with:
```bash
gh secret set SPOTIFY_CLIENT_ID --env kurl_env --body "..."
```

See [CI.md](CI.md) for full workflow reference.
