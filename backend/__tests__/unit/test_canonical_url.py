"""
Tests for utils.canonical_url -- builds platform URLs from ids.
"""

from utils.canonical_url import build_album_url, build_artist_url, build_track_url


class TestBuildTrackUrl:
    def test_spotify(self):
        assert build_track_url("spotify", "ABC123") == "https://open.spotify.com/track/ABC123"

    def test_deezer(self):
        assert build_track_url("deezer", "1234567") == "https://www.deezer.com/track/1234567"

    def test_tidal(self):
        assert build_track_url("tidal", "99999") == "https://tidal.com/track/99999"

    def test_youtube_music(self):
        assert build_track_url("youtubeMusic", "abc123") == "https://music.youtube.com/watch?v=abc123"

    def test_apple_music_standalone_song_uses_default_storefront(self):
        assert build_track_url("appleMusic", "999") == "https://music.apple.com/us/song/_/999"

    def test_apple_music_standalone_song_respects_country(self):
        assert build_track_url("appleMusic", "999", "gb") == "https://music.apple.com/gb/song/_/999"

    def test_apple_music_track_within_album_uses_album_template(self):
        assert build_track_url("appleMusic", "999", "au", "888") == "https://music.apple.com/au/album/_/888?i=999"

    def test_amazon_track_with_album_uses_trackAsin(self):
        assert (
            build_track_url("amazonMusic", "TRACK123", None, "ALB999")
            == "https://music.amazon.com/albums/ALB999?trackAsin=TRACK123"
        )

    def test_amazon_track_without_album_falls_to_album_id_shape(self):
        # Amazon tracks always live inside albums, so without album_id,
        # the track id gets used as album id (best-effort fallback).
        assert build_track_url("amazonMusic", "ALB123") == "https://music.amazon.com/albums/ALB123"

    def test_unknown_platform_returns_empty(self):
        assert build_track_url("foobar", "x") == ""


class TestBuildAlbumUrl:
    def test_spotify(self):
        assert build_album_url("spotify", "ABC") == "https://open.spotify.com/album/ABC"

    def test_apple_music_uses_storefront(self):
        assert build_album_url("appleMusic", "123", "au") == "https://music.apple.com/au/album/_/123"

    def test_unknown_platform_returns_empty(self):
        assert build_album_url("foobar", "x") == ""


class TestBuildArtistUrl:
    def test_tidal(self):
        assert build_artist_url("tidal", "99") == "https://tidal.com/artist/99"

    def test_apple_music_uses_storefront_default(self):
        assert build_artist_url("appleMusic", "55") == "https://music.apple.com/us/artist/_/55"

    def test_unknown_platform_returns_empty(self):
        assert build_artist_url("foobar", "x") == ""
