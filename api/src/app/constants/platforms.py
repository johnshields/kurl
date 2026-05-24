"""Platform identifiers, display names, URL templates, routing sets."""

PLATFORMS = {
    "spotify",
    "appleMusic",
    "youtubeMusic",
    "soundcloud",
    "beatport",
    "bandcamp",
    "amazonMusic",
    "tidal",
    "deezer",
}

PLATFORM_NAMES = {
    "spotify": "Spotify",
    "appleMusic": "Apple Music",
    "youtubeMusic": "YouTube Music",
    "soundcloud": "SoundCloud",
    "beatport": "Beatport",
    "bandcamp": "Bandcamp",
    "amazonMusic": "Amazon Music",
    "tidal": "Tidal",
    "deezer": "Deezer",
}

# Platforms with direct ISRC/UPC lookup.
ISRC_PLATFORMS = {"spotify", "appleMusic", "deezer", "tidal", "soundcloud"}

# Targets needing rescue resolution (iTunes, MusicBrainz, Last.fm).
RESCUE_PLATFORMS = {"spotify", "appleMusic", "youtubeMusic"}

# Odesli pair-routing rules.
ODESLI_UNSUPPORTED_TARGETS = frozenset({"beatport", "bandcamp"})
ODESLI_UNRELIABLE_SOURCES = frozenset({"soundcloud"})

# Short-link redirect hosts.
SHORT_LINK_HOSTS = {"spotify.link", "dzr.page.link", "on.soundcloud.com"}

# Lookup: URL_TEMPLATES[platform][kind] where kind in
# {track, album, artist, search, track_in_album}. track_in_album is for
# Apple/Amazon where track URLs embed parent album ID.
URL_TEMPLATES = {
    "spotify": {
        "track": "https://open.spotify.com/track/{id}",
        "album": "https://open.spotify.com/album/{id}",
        "artist": "https://open.spotify.com/artist/{id}",
        "search": "https://open.spotify.com/search/{query}",
    },
    "appleMusic": {
        "track": "https://music.apple.com/{country}/song/_/{id}",
        "track_in_album": "https://music.apple.com/{country}/album/_/{album_id}?i={id}",
        "album": "https://music.apple.com/{country}/album/_/{id}",
        "artist": "https://music.apple.com/{country}/artist/_/{id}",
        "search": "https://music.apple.com/us/search?term={query}",
    },
    "youtubeMusic": {
        "track": "https://music.youtube.com/watch?v={id}",
        "search": "https://music.youtube.com/search?q={query}",
    },
    "soundcloud": {
        "track": "https://soundcloud.com/{id}",
        "album": "https://soundcloud.com/{id}",
        "artist": "https://soundcloud.com/{id}",
        "search": "https://soundcloud.com/search?q={query}",
    },
    "beatport": {
        "track": "https://www.beatport.com/track/_/{id}",
        "album": "https://www.beatport.com/release/_/{id}",
        "artist": "https://www.beatport.com/artist/_/{id}",
        "search": "https://www.beatport.com/search?q={query}",
    },
    "bandcamp": {
        "track": "https://{id}",
        "album": "https://{id}",
        "artist": "https://{id}.bandcamp.com",
        "search": "https://bandcamp.com/search?q={query}",
    },
    "amazonMusic": {
        "track": "https://music.amazon.com/albums/{id}",
        "track_in_album": "https://music.amazon.com/albums/{album_id}?trackAsin={id}",
        "album": "https://music.amazon.com/albums/{id}",
        "artist": "https://music.amazon.com/artists/{id}",
        "search": "https://music.amazon.com/search/{query}",
    },
    "tidal": {
        "track": "https://tidal.com/track/{id}",
        "album": "https://tidal.com/album/{id}",
        "artist": "https://tidal.com/artist/{id}",
        "search": "https://tidal.com/search/{query}",
    },
    "deezer": {
        "track": "https://www.deezer.com/track/{id}",
        "album": "https://www.deezer.com/album/{id}",
        "artist": "https://www.deezer.com/artist/{id}",
        "search": "https://www.deezer.com/search/{query}",
    },
}
