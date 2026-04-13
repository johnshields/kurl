# ISRC Resolver Plan

Move off Odesli for the four big platforms by matching on ISRC directly.

## Why

Odesli's free tier is ~10 req/min and they've stopped handing out API keys. Not viable past a handful of users. Direct platform APIs give us thousands of requests per hour for free, plus full control over matching quality.

## How it works

Every properly distributed track has the same **ISRC** (International Standard Recording Code) on every platform. The flow:

1. Detect incoming URL's platform (regex on hostname)
2. Call that platform's API to get the track's ISRC
3. Call the target platform's API to search by ISRC
4. Return the matched URL

## Coverage

| Platform | Get ISRC from link | Search by ISRC | Phase |
|---|---|---|---|
| Spotify | yes (`external_ids.isrc`) | yes (`isrc:` filter) | 1 |
| Apple Music | yes (track metadata) | yes (batch up to 25) | 1 |
| Deezer | yes (track object) | yes (undocumented `/track/isrc:`) | 2 |
| Tidal | yes (track metadata) | yes | 2 |
| YouTube Music | no | no | fallback (fuzzy match on title + artist) |
| Amazon Music | no public API | no | Odesli fallback or drop |
| Pandora | no public API | no | Odesli fallback or drop |

## Phase 1 — Spotify + Apple Music

Covers the majority of real sharing. Smallest viable first step.

### Auth

- **Spotify** — client credentials flow (no user login). Register app at developer.spotify.com. Needs `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`. Token expires every hour; cache with refresh.
- **Apple Music** — JWT signed with private key (Apple Developer program required). Needs `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY`. Token valid up to 6 months; regenerate as needed.

### Files to add

```
backend/clients/
  spotify.py           # OAuth token + track/search endpoints
  apple_music.py       # JWT + track/search endpoints

backend/api/services/
  urls.py              # existing — coordinates resolver

backend/utils/
  url_parser.py        # detect platform from URL, extract track id
```

### Resolver flow (pseudocode)

```python
async def resolve_url(url, target):
    source = detect_platform(url)      # 'spotify' | 'appleMusic' | ...
    track_id = extract_track_id(url, source)

    isrc = await get_isrc(source, track_id)
    if not isrc:
        return fallback_to_odesli(url, target)

    match = await search_by_isrc(target, isrc)
    if not match:
        return fallback_to_odesli(url, target)

    return match
```

### Config additions

```
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
APPLE_TEAM_ID=
APPLE_KEY_ID=
APPLE_PRIVATE_KEY=
```

## Phase 2 — Deezer + Tidal

Add after phase 1 is stable.

- **Deezer** — no auth needed for public endpoints. Undocumented `/track/isrc:{code}` works today. Watch for breakage.
- **Tidal** — dev portal registration, OAuth client credentials.

## Fallback strategy

For any platform not in the resolver:
1. Try our own resolver first
2. If source or target isn't supported, fall back to Odesli
3. If Odesli fails too, return 404 with clear error

This gives the best of both worlds — no rate limits on the common case, full coverage via Odesli for the edge cases.

## Metadata

ISRC lookups also return track title and artist cheaply. No separate metadata call needed.

## Risks

- **Spotify rate limits** — generous but not infinite. Cache aggressively.
- **Apple Music JWT** — private key leak is bad. Store in env, never log.
- **Deezer undocumented endpoint** — could disappear. Have a fallback.
- **ISRC mismatches** — rare but real (re-releases, different masters). Cache the result to avoid repeated failures.

## Success criteria

- Resolve a Spotify link to Apple Music without calling Odesli
- Resolve an Apple Music link to Spotify without calling Odesli
- Sub-500ms p50 including cache miss
- No rate limit errors under normal load

## Open questions

- Do we need per-user Spotify auth later (for premium features)? Affects auth choice now.
- What do we do when ISRC exists but track is region-locked on target platform? (Out of scope for phase 1 — accept the link works but may not play.)
