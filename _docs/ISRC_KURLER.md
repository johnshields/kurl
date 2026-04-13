# ISRC Kurler Plan

Move off Odesli for the four big platforms by matching on universal identifiers (ISRC for tracks, UPC for albums).

## Current state

Already shipped in the prototype and feeding into the kurler plan:

- **URL parser** — [utils/url_parser.py](../backend/utils/url_parser.py) extracts `(platform, track_id)` from Spotify / Apple Music / YouTube Music / Deezer / Tidal / Amazon Music track URLs.
- **Odesli by-id calls** — [clients/odesli.py](../backend/clients/odesli.py) calls Odesli with `platform + type + id` instead of raw URL for more precise matching, with 3x retry + 1s/2s/4s backoff on 429.
- **Metadata scraping** — [clients/metadata.py](../backend/clients/metadata.py) scrapes source URLs for title and artist when Odesli is unavailable (Spotify `/embed/track/{id}` `__NEXT_DATA__`, Apple Music OG tags).
- **Search URL fallback** — [utils/search_url.py](../backend/utils/search_url.py) builds a target-platform search URL (Spotify, Apple Music) when no direct match exists. Returns `via: "search"` so the UI can show "Search on X" instead of "Open on X".
- **Tracking param stripping** — [utils/url.py](../backend/utils/url.py) removes `si`, `utm_*`, `fbclid`, etc. before hashing and before calling Odesli.

What's still missing for a full ISRC kurler: direct Spotify / Apple Music / Deezer / Tidal API clients that return and search by ISRC.

## Why

Odesli's free tier is ~10 req/min and they've stopped handing out API keys. Not viable past a handful of users. Direct platform APIs give us thousands of requests per hour for free, plus full control over matching quality.

## Entity types and identifiers

Music URLs fall into three entity types, each with its own cross-platform identifier:

| Entity | Universal ID | Fallback |
|---|---|---|
| Track | **ISRC** (International Standard Recording Code) | artist + title fuzzy match |
| Album | **UPC/EAN** (Universal Product Code / European Article Number) | artist + album title fuzzy match |
| Artist | None universal | name match (or MusicBrainz lookup) |

ISRC/UPC are guaranteed identical across platforms when the distributor tagged properly. Artists have no universal ID — hardest to match reliably.

## URL formats (researched)

Parsing table for all common formats. `{id}` is the platform identifier, `{country}` is a 2-letter code.

### Spotify

| Entity | Pattern | Example |
|---|---|---|
| Track | `open.spotify.com/track/{id}` | `open.spotify.com/track/6QJVQSuMC77psM4vgPo31D` |
| Album | `open.spotify.com/album/{id}` | `open.spotify.com/album/1DFixLWuPkv3KT3TnV35m3` |
| Artist | `open.spotify.com/artist/{id}` | `open.spotify.com/artist/3TVXtAsR1Inumwj472S9r4` |
| URI | `spotify:{type}:{id}` | `spotify:track:6QJVQSuMC77psM4vgPo31D` |
| Short | `spotify.link/{random}` | `spotify.link/abc123XYZ` (client-side JS redirect — untracker) |

Tracking params: `?si=` (shareable identifier). Already stripped.

### Apple Music

| Entity | Pattern | Example |
|---|---|---|
| Track | `music.apple.com/{country}/album/{slug}/{album_id}?i={track_id}` | `music.apple.com/au/album/day-one/1791161215?i=1791161543` |
| Album | `music.apple.com/{country}/album/{slug}/{album_id}` (no `?i=`) | `music.apple.com/au/album/day-one/1791161215` |
| Artist | `music.apple.com/{country}/artist/{slug}/{artist_id}` | `music.apple.com/au/artist/adele/262836961` |

**Critical**: Apple Music tracks have no standalone URL — a track IS an album URL with `?i=<track_id>`. The `i` query param is the track ID; the path segment is the album ID.

### YouTube Music

| Entity | Pattern | Notes |
|---|---|---|
| Track | `music.youtube.com/watch?v={video_id}` | Video ID; may also have `&list=` |
| Playlist | `music.youtube.com/playlist?list={playlist_id}` | YouTube Music treats albums as playlists |
| Artist | `music.youtube.com/channel/{channel_id}` | |
| Short | `youtu.be/{video_id}` | Maps to `watch?v={id}` |

**Gotcha**: YouTube Music doesn't cleanly distinguish tracks from albums — albums are typed playlists. ISRC match isn't supported natively. Deferred to fuzzy-match fallback.

### Deezer

| Entity | Pattern | Example |
|---|---|---|
| Track | `deezer.com/track/{id}` or `deezer.com/{country}/track/{id}` | `deezer.com/track/1234567` |
| Album | `deezer.com/album/{id}` or `deezer.com/{country}/album/{id}` | `deezer.com/album/987654` |
| Artist | `deezer.com/artist/{id}` | `deezer.com/artist/55555` |
| Short | `dzr.page.link/{id}` | Follow redirect to canonical |

Country prefix is optional. Handle the `dzr.page.link` short form via HTTP redirect follow.

### Tidal

| Entity | Pattern | Example |
|---|---|---|
| Track | `tidal.com/track/{id}` or `tidal.com/browse/track/{id}` | `tidal.com/track/12345` |
| Album | `tidal.com/album/{id}` | `tidal.com/album/67890` |
| Artist | `tidal.com/artist/{id}` | `tidal.com/artist/11111` |
| Listen | `listen.tidal.com/{type}/{id}` | Authenticated player URL |

### Amazon Music

| Entity | Pattern | Example |
|---|---|---|
| Track | `music.amazon.com/albums/{album_id}?trackAsin={track_id}` | `music.amazon.com/albums/B0042GBQS8?trackAsin=B0042GB...` |
| Album | `music.amazon.com/albums/{album_id}` | `music.amazon.com/albums/B0042GBQS8` |
| Artist | `music.amazon.com/artists/{artist_id}` | |

**Gotcha**: Same as Apple Music — tracks live inside albums, referenced by `?trackAsin=`. IDs are 10-char alphanumeric (ASINs).

No public API for ISRC search. Deferred to fuzzy-match fallback.

## Phased rollout

### Phase 1.1 — Tracks (ISRC)

Covers 80%+ of real sharing. Start here.

**Supported:** Spotify, Apple Music, Deezer, Tidal (all four support ISRC search).
**Deferred fallback:** YouTube Music, Amazon Music, Pandora (via Odesli or the search-URL fallback that's already in place).

Flow:
```
1. Parse URL → (platform, entity_type="track", track_id)   [done]
2. Call source platform API → get ISRC                      [needs spotify/apple/deezer/tidal clients]
3. Call target platform API with ISRC → get matched URL     [needs spotify/apple/deezer/tidal clients]
4. Return match
```

### Phase 1.2 — Albums (UPC)

Same four platforms support UPC search on album endpoints. Adds Apple Music album → Spotify album and equivalents.

Flow:
```
1. Parse URL → (platform, entity_type="album", album_id)
2. Call source platform API → get UPC
3. Call target platform API with UPC → get matched album URL
4. Return match
```

### Phase 1.3 — Artists (name match)

No universal ID. Use name-based search and pick the best match.

Flow:
```
1. Parse URL → (platform, entity_type="artist", artist_id)
2. Call source platform API → get artist name + optional external IDs (MusicBrainz, Wikipedia)
3. Call target platform search API with name
4. Pick top result (confidence check on popularity / verified status)
5. Return match
```

Lower accuracy — artists with the same name will be ambiguous. Accept ~90% match rate for phase 1.3, surface "could not confidently match" as a soft error in the UI.

## Architecture

### New files

```
backend/clients/
  spotify.py           # OAuth client creds + track/album/artist endpoints
  apple_music.py       # JWT + track/album/artist endpoints
  deezer.py            # No auth + track/album/artist endpoints (phase 1.2)
  tidal.py             # OAuth + track/album/artist endpoints (phase 1.2)

backend/utils/
  url_parser.py        # [done] parse any streaming URL → (platform, entity_type, id)
  kurler.py            # coordinates source → target resolution per entity

backend/api/services/
  urls.py              # [done] entry point, calls kurler with Odesli fallback
```

### URL parser signature (expanded)

Current parser returns `(platform, track_id)`. To support albums and artists, expand to:

```python
@dataclass
class ParsedMusicUrl:
    platform: str           # 'spotify', 'appleMusic', 'deezer', etc.
    entity_type: str        # 'track', 'album', 'artist'
    id: str                 # platform-specific ID
    country: str | None     # Apple Music / Deezer country code
    album_id: str | None    # for Apple Music/Amazon tracks (parent album)

def parse_music_url(url: str) -> ParsedMusicUrl | None:
    ...
```

### Kurler signature

```python
async def kurl(
    source: ParsedMusicUrl,
    target_platform: str,
) -> KurlMatch | None:
    # For tracks: get ISRC from source, search target by ISRC
    # For albums: get UPC from source, search target by UPC
    # For artists: get name from source, search target by name
    ...
```

## Auth

| Platform | Auth | Credentials | Token lifetime |
|---|---|---|---|
| Spotify | OAuth client credentials | `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` | 1 hour (cache + refresh) |
| Apple Music | JWT (ES256) | `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY` | Up to 6 months |
| Deezer | None (public endpoints) | — | N/A |
| Tidal | OAuth client credentials | `TIDAL_CLIENT_ID`, `TIDAL_CLIENT_SECRET` | Varies |

## Fallback strategy

Current order (already in the prototype):

1. Parse URL → known platform? If no, call Odesli by-URL.
2. Parsed → call Odesli by-id (with retry on 429).
3. Odesli has target platform link? Return it.
4. Odesli has no target link but has metadata? Build search URL on target platform.
5. Odesli failed entirely (after retries)? Scrape source URL for title + artist → build search URL.
6. No metadata anywhere? 404.

When the kurler phases land, inserted between steps 1 and 2:

- Try direct source → ISRC lookup
- Try target ISRC → URL search
- Only fall to Odesli if either fails

This keeps the fast path fast and makes Odesli a long-tail fallback instead of the primary.

## Cache strategy

- **URL → target mapping** cached by `md5(normalised_url + target_platform)` — already in place, 24h TTL.
- **ISRC/UPC lookups** should be cached separately — `isrc:spotify:{track_id}` → ISRC. Avoids repeated calls for the same popular track.
- Separate cache namespace for negative results (short TTL, e.g. 15 min) so we don't hammer a broken match.

## Risks

- **Spotify rate limits** — generous but real. Cache ISRC lookups aggressively.
- **Apple Music JWT** — private key leak is catastrophic. Store in env, never log, rotate if exposed.
- **Deezer undocumented endpoint** — `/track/isrc:{code}` could disappear. Keep Odesli + search-URL fallback.
- **Spotify short links (`spotify.link`)** — client-side JS redirect, not followable with a simple HTTP GET. May require a headless fetch or rejection with "please use full link".
- **Regional ISRC mismatches** — rare, but re-releases sometimes get new ISRCs. Cache negative results short.
- **Album tracks with `?i=` differ by region** — an Apple Music track in `us` vs `au` may have different track IDs but the same ISRC. Normalise country before hashing.

## Success criteria

**Phase 1.1 (tracks):**
- Kurl Spotify track → Apple Music track without calling Odesli
- Kurl Apple Music track (`?i=`) → Spotify track without Odesli
- Kurl Deezer track → Spotify track
- Kurl Tidal track → Spotify track
- Sub-500ms p50 including cache miss
- No rate-limit errors under realistic load (100 rps burst)

**Phase 1.2 (albums):**
- Album URL on any supported platform → album URL on any other
- Apple Music album (no `?i=`) → Spotify album via UPC

**Phase 1.3 (artists):**
- Artist URL → artist URL on target with ≥90% accuracy on well-known artists

## Open questions

- **Short link resolution** (`spotify.link`, `dzr.page.link`): follow with a HEAD/GET and parse destination, or reject?
- **Region-specific availability**: do we surface "this track isn't available on Spotify in IE" or just return the link anyway?
- **MusicBrainz for artists**: worth adding as a disambiguation layer in phase 1.3?
