import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse


@dataclass
class ParsedTrack:
    """Backwards-compatible track-only result (used by existing code)."""

    platform: str
    track_id: str


@dataclass
class ParsedMusicUrl:
    """Expanded parse result supporting tracks, albums, and artists."""

    platform: str  # spotify, appleMusic, youtubeMusic, deezer, tidal, amazonMusic, soundcloud, beatport, bandcamp
    entity_type: str  # track, album, artist
    id: str  # platform-specific ID
    country: str | None = None  # Apple Music / Deezer country code
    album_id: str | None = None  # parent album for Apple Music / Amazon tracks


_SPOTIFY_TRACK = re.compile(r"/track/([A-Za-z0-9]+)")
_SPOTIFY_ALBUM = re.compile(r"/album/([A-Za-z0-9]+)")
_SPOTIFY_ARTIST = re.compile(r"/artist/([A-Za-z0-9]+)")

_APPLE_ALBUM_PATH = re.compile(r"/(?P<country>[a-z]{2})/album/[^/]+/(?P<album_id>\d+)")
_APPLE_ARTIST = re.compile(r"/(?P<country>[a-z]{2})/artist/[^/]+/(?P<artist_id>\d+)")

_DEEZER_TRACK = re.compile(r"/(?:[a-z]{2}/)?track/(\d+)")
_DEEZER_ALBUM = re.compile(r"/(?:[a-z]{2}/)?album/(\d+)")
_DEEZER_ARTIST = re.compile(r"/(?:[a-z]{2}/)?artist/(\d+)")

_TIDAL_TRACK = re.compile(r"/(?:browse/)?track/(\d+)")
_TIDAL_ALBUM = re.compile(r"/(?:browse/)?album/(\d+)")
_TIDAL_ARTIST = re.compile(r"/(?:browse/)?artist/(\d+)")

_AMAZON_ALBUM = re.compile(r"/albums/([A-Z0-9]+)")
_AMAZON_ARTIST = re.compile(r"/artists/([A-Z0-9]+)")

_YOUTUBE_HOSTS = ("music.youtube.com", "youtube.com", "www.youtube.com", "m.youtube.com")
_YOUTU_BE_PATH = re.compile(r"^/([A-Za-z0-9_-]{6,})")

_SC_RESERVED = frozenset(
    {
        "search",
        "you",
        "login",
        "upload",
        "stream",
        "tags",
        "people",
        "stations",
        "charts",
        "discover",
        "likes",
        "following",
        "followers",
        "tracks",
        "reposts",
        "sets",
    }
)

_SEARCH_PATTERNS = (
    re.compile(r"spotify\.com/search/"),
    re.compile(r"music\.apple\.com/.*/?search"),
    re.compile(r"music\.youtube\.com/search"),
    re.compile(r"deezer\.com/.*/?search"),
    re.compile(r"tidal\.com/.*/?search"),
    re.compile(r"music\.amazon\.com/.*/?search"),
    re.compile(r"soundcloud\.com/search"),
    re.compile(r"beatport\.com/search"),
    re.compile(r"bandcamp\.com/search"),
)


def is_search_url(url: str) -> bool:
    """Detect search result pages to fail fast with a friendly error."""
    return any(p.search(url) for p in _SEARCH_PATTERNS)


def parse_music_url(url: str) -> ParsedMusicUrl | None:
    """Parse a streaming URL into platform, entity type, and ID."""
    parts = urlparse(url)
    host = (parts.netloc or "").lower()
    path = parts.path or ""
    query = parse_qs(parts.query)

    if "spotify.com" in host:
        return _parse_spotify(path)

    if "music.apple.com" in host:
        return _parse_apple_music(path, query)

    if host == "youtu.be":
        return _parse_youtu_be(path)

    if any(h in host for h in _YOUTUBE_HOSTS):
        return _parse_youtube_music(query)

    if "deezer.com" in host:
        return _parse_deezer(path)

    if "tidal.com" in host or "listen.tidal.com" in host:
        return _parse_tidal(path)

    if "music.amazon" in host:
        return _parse_amazon(path, query)

    if "soundcloud.com" in host:
        return _parse_soundcloud(path)

    if "beatport.com" in host:
        return _parse_beatport(path)

    if host.endswith("bandcamp.com"):
        return _parse_bandcamp(host, path)

    return None


def parse_track(url: str) -> ParsedTrack | None:
    """Parse a streaming URL and return (platform, track_id) if it's a track.

    Kept for backwards compatibility with existing code.
    """
    parsed = parse_music_url(url)
    if parsed and parsed.entity_type == "track":
        return ParsedTrack(parsed.platform, parsed.id)
    return None


def _parse_spotify(path: str) -> ParsedMusicUrl | None:
    m = _SPOTIFY_TRACK.search(path)
    if m:
        return ParsedMusicUrl("spotify", "track", m.group(1))

    m = _SPOTIFY_ALBUM.search(path)
    if m:
        return ParsedMusicUrl("spotify", "album", m.group(1))

    m = _SPOTIFY_ARTIST.search(path)
    if m:
        return ParsedMusicUrl("spotify", "artist", m.group(1))

    return None


def _parse_apple_music(path: str, query: dict) -> ParsedMusicUrl | None:
    m = _APPLE_ARTIST.search(path)
    if m:
        return ParsedMusicUrl(
            "appleMusic",
            "artist",
            m.group("artist_id"),
            country=m.group("country"),
        )

    m = _APPLE_ALBUM_PATH.search(path)
    if m:
        country = m.group("country")
        album_id = m.group("album_id")
        track_id = query.get("i", [None])[0]

        if track_id:
            return ParsedMusicUrl(
                "appleMusic",
                "track",
                track_id,
                country=country,
                album_id=album_id,
            )
        return ParsedMusicUrl("appleMusic", "album", album_id, country=country)

    return None


def _parse_youtube_music(query: dict) -> ParsedMusicUrl | None:
    video_id = query.get("v", [None])[0]
    if video_id:
        return ParsedMusicUrl("youtubeMusic", "track", video_id)

    list_id = query.get("list", [None])[0]
    if list_id:
        return ParsedMusicUrl("youtubeMusic", "album", list_id)

    return None


def _parse_youtu_be(path: str) -> ParsedMusicUrl | None:
    m = _YOUTU_BE_PATH.match(path)
    if m:
        return ParsedMusicUrl("youtubeMusic", "track", m.group(1))
    return None


def _parse_deezer(path: str) -> ParsedMusicUrl | None:
    m = _DEEZER_TRACK.search(path)
    if m:
        return ParsedMusicUrl("deezer", "track", m.group(1))

    m = _DEEZER_ALBUM.search(path)
    if m:
        return ParsedMusicUrl("deezer", "album", m.group(1))

    m = _DEEZER_ARTIST.search(path)
    if m:
        return ParsedMusicUrl("deezer", "artist", m.group(1))

    return None


def _parse_tidal(path: str) -> ParsedMusicUrl | None:
    m = _TIDAL_TRACK.search(path)
    if m:
        return ParsedMusicUrl("tidal", "track", m.group(1))

    m = _TIDAL_ALBUM.search(path)
    if m:
        return ParsedMusicUrl("tidal", "album", m.group(1))

    m = _TIDAL_ARTIST.search(path)
    if m:
        return ParsedMusicUrl("tidal", "artist", m.group(1))

    return None


def _parse_soundcloud(path: str) -> ParsedMusicUrl | None:
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None

    user = parts[0]
    if user in _SC_RESERVED:
        return None

    if len(parts) == 1:
        return ParsedMusicUrl("soundcloud", "artist", user)

    if len(parts) >= 3 and parts[1] == "sets":
        return ParsedMusicUrl("soundcloud", "album", f"{user}/sets/{parts[2]}")

    if len(parts) == 2 and parts[1] not in _SC_RESERVED:
        return ParsedMusicUrl("soundcloud", "track", f"{user}/{parts[1]}")

    return None


def _parse_amazon(path: str, query: dict) -> ParsedMusicUrl | None:
    m = _AMAZON_ALBUM.search(path)
    if m:
        album_id = m.group(1)
        track_asin = query.get("trackAsin", [None])[0]

        if track_asin:
            return ParsedMusicUrl(
                "amazonMusic",
                "track",
                track_asin,
                album_id=album_id,
            )
        return ParsedMusicUrl("amazonMusic", "album", album_id)

    m = _AMAZON_ARTIST.search(path)
    if m:
        return ParsedMusicUrl("amazonMusic", "artist", m.group(1))

    return None


_BEATPORT_TRACK = re.compile(r"/track/[^/]+/(\d+)")
_BEATPORT_ALBUM = re.compile(r"/release/[^/]+/(\d+)")
_BEATPORT_ARTIST = re.compile(r"/artist/[^/]+/(\d+)")


def _parse_beatport(path: str) -> ParsedMusicUrl | None:
    # URL structure: /track/{slug}/{numeric_id}, /release/{slug}/{id}, /artist/{slug}/{id}
    m = _BEATPORT_TRACK.search(path)
    if m:
        return ParsedMusicUrl("beatport", "track", m.group(1))

    m = _BEATPORT_ALBUM.search(path)
    if m:
        return ParsedMusicUrl("beatport", "album", m.group(1))

    m = _BEATPORT_ARTIST.search(path)
    if m:
        return ParsedMusicUrl("beatport", "artist", m.group(1))

    return None


def _parse_bandcamp(host: str, path: str) -> ParsedMusicUrl | None:
    # URL structure: {artist}.bandcamp.com/track/{slug} or /album/{slug}.
    # Bare {artist}.bandcamp.com is the artist page. ID stored as full
    # host+path so canonical reconstruction needs no extra lookup.
    parts = [p for p in path.split("/") if p]

    if not parts:
        # Artist page: id = subdomain (without .bandcamp.com)
        artist = host.removesuffix(".bandcamp.com")
        if artist and artist != "bandcamp" and artist != "www":
            return ParsedMusicUrl("bandcamp", "artist", artist)
        return None

    if len(parts) >= 2 and parts[0] in ("track", "album"):
        kind = "track" if parts[0] == "track" else "album"
        return ParsedMusicUrl("bandcamp", kind, f"{host}/{parts[0]}/{parts[1]}")

    return None
