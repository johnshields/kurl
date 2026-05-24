"""
Tests for utils.url_parser -- the URL to (platform, entity_type, id) mapper.
Most critical correctness surface in the codebase.
"""

from utils.url.url_parser import (
    ParsedMusicUrl,
    ParsedTrack,
    is_search_url,
    parse_music_url,
    parse_track,
)


class TestSpotify:
    def test_track_url(self):
        r = parse_music_url("https://open.spotify.com/track/6QJVQSuMC77psM4vgPo31D")
        assert r == ParsedMusicUrl("spotify", "track", "6QJVQSuMC77psM4vgPo31D")

    def test_album_url(self):
        r = parse_music_url("https://open.spotify.com/album/1DFixLWuPkv3KT3TnV35m3")
        assert r == ParsedMusicUrl("spotify", "album", "1DFixLWuPkv3KT3TnV35m3")

    def test_artist_url(self):
        r = parse_music_url("https://open.spotify.com/artist/3TVXtAsR1Inumwj472S9r4")
        assert r == ParsedMusicUrl("spotify", "artist", "3TVXtAsR1Inumwj472S9r4")

    def test_track_with_si_tracking_param(self):
        r = parse_music_url("https://open.spotify.com/track/6QJVQSuMC77psM4vgPo31D?si=abc123")
        assert r is not None
        assert r.id == "6QJVQSuMC77psM4vgPo31D"


class TestAppleMusic:
    def test_track_url_with_country_and_album(self):
        r = parse_music_url("https://music.apple.com/au/album/day-one/1791161215?i=1791161543")
        assert r == ParsedMusicUrl(
            "appleMusic",
            "track",
            "1791161543",
            country="au",
            album_id="1791161215",
        )

    def test_album_url_without_track_param(self):
        r = parse_music_url("https://music.apple.com/au/album/day-one/1791161215")
        assert r == ParsedMusicUrl("appleMusic", "album", "1791161215", country="au")

    def test_artist_url(self):
        r = parse_music_url("https://music.apple.com/au/artist/adele/262836961")
        assert r == ParsedMusicUrl(
            "appleMusic",
            "artist",
            "262836961",
            country="au",
        )

    def test_different_country_storefront(self):
        r = parse_music_url("https://music.apple.com/gb/album/x/999?i=888")
        assert r.country == "gb"

    def test_song_url_standalone(self):
        r = parse_music_url("https://music.apple.com/us/song/never-gonna-give-you-up/1452408575")
        assert r == ParsedMusicUrl("appleMusic", "track", "1452408575", country="us")

    def test_song_url_no_country(self):
        r = parse_music_url("https://music.apple.com/song/x/123")
        assert r == ParsedMusicUrl("appleMusic", "track", "123")


class TestYouTube:
    def test_youtu_be_short_link(self):
        r = parse_music_url("https://youtu.be/Cl6Rz1Uvi2M")
        assert r == ParsedMusicUrl("youtubeMusic", "track", "Cl6Rz1Uvi2M")

    def test_music_youtube_watch(self):
        r = parse_music_url("https://music.youtube.com/watch?v=abc123XYZ")
        assert r == ParsedMusicUrl("youtubeMusic", "track", "abc123XYZ")

    def test_regular_youtube_watch(self):
        r = parse_music_url("https://www.youtube.com/watch?v=Cl6Rz1Uvi2M")
        assert r == ParsedMusicUrl("youtubeMusic", "track", "Cl6Rz1Uvi2M")

    def test_playlist_treated_as_album(self):
        r = parse_music_url("https://music.youtube.com/playlist?list=PLxyz")
        assert r is not None
        assert r.entity_type == "album"

    def test_watch_with_list_param_prefers_track(self):
        r = parse_music_url("https://music.youtube.com/watch?v=abc&list=PL123")
        assert r.entity_type == "track"


class TestDeezer:
    def test_track_url(self):
        r = parse_music_url("https://deezer.com/track/1234567")
        assert r == ParsedMusicUrl("deezer", "track", "1234567")

    def test_country_prefixed_track_url(self):
        r = parse_music_url("https://www.deezer.com/en/track/1234567")
        assert r is not None
        assert r.id == "1234567"

    def test_album_url(self):
        r = parse_music_url("https://www.deezer.com/album/987654")
        assert r == ParsedMusicUrl("deezer", "album", "987654")


class TestTidal:
    def test_track_url(self):
        r = parse_music_url("https://tidal.com/track/12345")
        assert r == ParsedMusicUrl("tidal", "track", "12345")

    def test_browse_prefix(self):
        r = parse_music_url("https://tidal.com/browse/track/12345")
        assert r is not None
        assert r.id == "12345"


class TestAmazonMusic:
    def test_track_url(self):
        r = parse_music_url("https://music.amazon.com/albums/B0042GBQS8?trackAsin=B0042GB123")
        assert r == ParsedMusicUrl(
            "amazonMusic",
            "track",
            "B0042GB123",
            album_id="B0042GBQS8",
        )

    def test_album_url_without_track(self):
        r = parse_music_url("https://music.amazon.com/albums/B0042GBQS8")
        assert r == ParsedMusicUrl("amazonMusic", "album", "B0042GBQS8")


class TestUnknownAndInvalid:
    def test_unknown_domain_returns_none(self):
        assert parse_music_url("https://bandcamp.com/track/abc") is None

    def test_malformed_url_returns_none(self):
        assert parse_music_url("not-a-url") is None

    def test_empty_string(self):
        assert parse_music_url("") is None


class TestParseTrackBackwardsCompat:
    def test_returns_parsed_track_for_tracks(self):
        r = parse_track("https://open.spotify.com/track/ABC123")
        assert r == ParsedTrack("spotify", "ABC123")

    def test_returns_none_for_albums(self):
        assert parse_track("https://open.spotify.com/album/XYZ") is None

    def test_returns_none_for_artists(self):
        assert parse_track("https://open.spotify.com/artist/XYZ") is None


class TestIsSearchUrl:
    def test_spotify_search_is_detected(self):
        assert is_search_url("https://open.spotify.com/search/foo")

    def test_apple_search_is_detected(self):
        assert is_search_url("https://music.apple.com/us/search?term=foo")

    def test_youtube_search_is_detected(self):
        assert is_search_url("https://music.youtube.com/search?q=foo")

    def test_track_url_is_not_search(self):
        assert not is_search_url("https://open.spotify.com/track/abc")
