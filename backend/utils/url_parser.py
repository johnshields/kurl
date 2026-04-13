import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse


@dataclass
class ParsedTrack:
    platform: str  # Odesli key: spotify, appleMusic, youtubeMusic, deezer, tidal, amazonMusic
    track_id: str


_SPOTIFY_TRACK = re.compile(r"/track/([A-Za-z0-9]+)")
_APPLE_ALBUM = re.compile(r"/album/[^/]+/\d+")
_DEEZER_TRACK = re.compile(r"/track/(\d+)")
_TIDAL_TRACK = re.compile(r"/track/(\d+)")
_AMAZON_ALBUM = re.compile(r"/albums/([A-Z0-9]+)")
_YOUTUBE_MUSIC = ("music.youtube.com",)


def parse_track(url: str) -> ParsedTrack | None:
    """Parse a streaming URL and return (platform, track_id) if it's a track."""
    parts = urlparse(url)
    host = (parts.netloc or "").lower()
    path = parts.path or ""
    query = parse_qs(parts.query)

    if "spotify.com" in host:
        m = _SPOTIFY_TRACK.search(path)
        if m:
            return ParsedTrack("spotify", m.group(1))
        return None

    if "music.apple.com" in host:
        # Track = album URL with ?i=<track_id>
        track_id = query.get("i", [None])[0]
        if track_id and _APPLE_ALBUM.search(path):
            return ParsedTrack("appleMusic", track_id)
        return None

    if any(h in host for h in _YOUTUBE_MUSIC):
        video_id = query.get("v", [None])[0]
        if video_id:
            return ParsedTrack("youtubeMusic", video_id)
        return None

    if "deezer.com" in host:
        m = _DEEZER_TRACK.search(path)
        if m:
            return ParsedTrack("deezer", m.group(1))
        return None

    if "tidal.com" in host:
        m = _TIDAL_TRACK.search(path)
        if m:
            return ParsedTrack("tidal", m.group(1))
        return None

    if "music.amazon" in host:
        # Track = album URL with ?trackAsin=<id>
        track_asin = query.get("trackAsin", [None])[0]
        if track_asin and _AMAZON_ALBUM.search(path):
            return ParsedTrack("amazonMusic", track_asin)
        return None

    return None
