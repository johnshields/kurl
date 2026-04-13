# Roadmap

## Supported platforms (phase 1)

- Spotify
- Apple Music
- YouTube Music
- Deezer
- Tidal
- Amazon Music
- Pandora

All matched via ISRC through Odesli - no direct API deals needed.

---

## Phase 1 - anonymous MVP

- [ ] Flutter share extension on iOS and Android
- [ ] Platform picker UI
- [ ] FastAPI `/api/kurl` endpoint
- [ ] Odesli integration
- [ ] Redis caching
- [ ] System share sheet handoff
- [ ] Preferred platform saved locally (SQLite)
- [ ] App Store + Play Store submission

## Phase 2 - social layer

- [ ] Accounts (email or Sign in with Apple/Google)
- [ ] Friend list with saved platform prefs
- [ ] One-tap share to a known friend
- [ ] Postgres backend for user/friend graph
- [ ] Friend invite flow
