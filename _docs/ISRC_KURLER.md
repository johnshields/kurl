# ISRC Kurler

Direct-to-platform URL resolution via universal identifiers. Skips Odesli entirely for the common cases, fast and rate-limit-free.

## Platform clients

Per-platform clients live in `backend/clients/platforms/`.

| Platform | Auth | ISRC | UPC | Name search |
|---|---|---|---|---|
| Spotify | OAuth client creds | `external_ids.isrc` | `external_ids.upc` | `search?q=track:X artist:Y` |
| Apple Music | JWT (ES256) | `attributes.isrc` | `attributes.upc` | `search?term=` |
| Deezer | none (public) | `isrc` | `upc` | `/search/track?q=` |
| Tidal (v2) | OAuth client creds | `attributes.isrc` | `attributes.barcodeId` | `/searchResults/{q}` (JSON:API) |
| Amazon Music | - | no public API | no public API | - |
| YouTube Music | - | no public API | - | - |
| Beatport | - | partner-only API | - | - |
| Bandcamp | - | API deprecated 2014 | - | - |

## Flow

```
1. Parse URL → ParsedMusicUrl(platform, entity_type, id, [country, album_id])
2. Cache hit? Return.
3. KURLER (fast path):
   a. If source has an API client: fetch ISRC/UPC from source
      → search target by identifier → return (via=isrc or via=upc)
   b. If (a) fails: scrape metadata from source (oEmbed / NEXT_DATA / OG tags)
      → search target by title+artist → return (via=search_api)
4. ODESLI fallback: by-id or by-url, 3× retry w/ backoff
5. SEARCH URL fallback: build deep-link into target's search page (via=search)
6. 404: no metadata available anywhere
```

Entry point: `utils/kurler.py::kurl(source, target_platform)`. Service wrapper: `api/services/urls.py`.

## Client interface

Every platform module exposes the same surface (removes all `hasattr` branching from the orchestrator):

```python
# Fetches
async def get_track(id, **ctx) -> dict
async def get_album(id, **ctx) -> dict
async def get_artist(id, **ctx) -> dict
async def search_by_isrc(isrc, **ctx) -> dict | None
async def search_by_upc(upc, **ctx) -> dict | None
async def search_track(title, artist, **ctx) -> dict | None
async def search_artist(name, **ctx) -> dict | None

# Extracts
def extract_isrc(track) -> str | None
def extract_upc(album) -> str | None
def extract_track_url(track) -> str | None
def extract_album_url(album) -> str | None
def extract_artist_url(artist) -> str | None
def extract_metadata(track) -> tuple[title, artist]
def extract_album_metadata(album) -> tuple[title, artist]
def extract_artist_name(artist) -> str | None

# Readiness
def is_configured() -> bool
```

`**ctx` is `{"storefront": "us"}` for Apple, empty for everyone else. The `_ctx()` helper in `kurler.py` threads it uniformly.

## URL parsing

`utils/url_parser.py::parse_music_url()` returns `ParsedMusicUrl` for:

- Spotify: `open.spotify.com/{track|album|artist}/{id}`
- Apple Music: `music.apple.com/{country}/album/{slug}/{album_id}[?i={track_id}]`, `/artist/{slug}/{id}`
- YouTube Music: `music.youtube.com/watch?v=`, `youtube.com/watch?v=`, `youtu.be/{id}`
- Deezer: `deezer.com/[{country}/]{track|album|artist}/{id}`, `dzr.page.link/{id}` (deferred)
- Tidal: `tidal.com/[browse/]{track|album|artist}/{id}`
- Amazon Music: `music.amazon.com/albums/{album_id}[?trackAsin={track_id}]`, `/artists/{id}`

Canonical URL reconstruction in `utils/canonical_url.py` + templates in `app/constants.py`.

## Auth

| Platform | Strategy | Token lifetime |
|---|---|---|
| Spotify | OAuth client_credentials | 1h, cached in-process |
| Apple Music | ES256 JWT signed with `.p8` private key | 12h (max 6mo per Apple) |
| Deezer | none | - |
| Tidal | OAuth client_credentials | 24h, cached |

Shared OAuth helper: `clients/platforms/_oauth.py::fetch_client_credentials_token()`.

## Tidal v2 gotchas

Tidal migrated from v1 → v2 (JSON:API) - v1 paths return 404. Things to know:

- Base URL: `https://openapi.tidal.com/v2` (not `/`)
- Accept header: `application/vnd.api+json` (not `vnd.tidal.v1+json`)
- Search endpoint: `/searchResults/{query}` - **camelCase**, not `/searchresults`
- Responses are JSON:API: `data.attributes.X`, relationships live in a sibling `included[]` array
- `relationships.tracks.data[]` is the ordered ID list; iterate `included[]` to find matching resources

## Risks

- **Spotify rate limits** - rolling 30s window, undocumented numbers. Cache aggressively.
- **Apple JWT private key** - leak = revoke + regenerate immediately.
- **Deezer ISRC endpoint is undocumented** (`/track/isrc:{code}`). Could disappear.
- **Tidal Dev Mode** - new apps start rate-limited; submit "Application Review" for production quotas.
- **Regional ISRC mismatches** - re-releases sometimes get new ISRCs; negative cache short (15 min).

## References

- Spotify Web API: https://developer.spotify.com/documentation/web-api
- Apple Music API: https://developer.apple.com/documentation/applemusicapi/
- Deezer API: https://developers.deezer.com/api
- Tidal Developer: https://developer.tidal.com/ / https://tidal-music.github.io/tidal-api-reference/
