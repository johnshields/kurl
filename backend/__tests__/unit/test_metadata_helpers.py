"""
Tests for pure helpers in clients.metadata -- YouTube title parsing and noise stripping.
No network calls; these are the deterministic pieces.
"""

from clients.metadata import _parse_youtube_title, _strip_youtube_noise


class TestParseYoutubeTitle:
    def test_artist_dash_title(self):
        assert _parse_youtube_title("Fred again.. - Delilah", "Fred") == ("Delilah", "Fred again..")

    def test_em_dash(self):
        assert _parse_youtube_title("Adele \u2014 Hello", "Adele") == ("Hello", "Adele")

    def test_en_dash(self):
        assert _parse_youtube_title("Adele \u2013 Hello", "Adele") == ("Hello", "Adele")

    def test_strips_official_music_video_suffix(self):
        title, artist = _parse_youtube_title("Adele - Hello (Official Music Video)", "Adele")
        assert title == "Hello"
        assert artist == "Adele"

    def test_no_dash_falls_back_to_author_name(self):
        title, artist = _parse_youtube_title("Hello", "Adele")
        assert title == "Hello"
        assert artist == "Adele"

    def test_strips_vevo_suffix_from_author(self):
        _, artist = _parse_youtube_title("Some Song", "AdeleVEVO")
        assert artist == "Adele"

    def test_strips_topic_suffix_from_author(self):
        _, artist = _parse_youtube_title("Some Song", "Adele - Topic")
        assert artist == "Adele"

    def test_no_author_no_artist(self):
        title, artist = _parse_youtube_title("Some Song", None)
        assert title == "Some Song"
        assert artist is None


class TestStripYoutubeNoise:
    def test_strips_official_music_video(self):
        assert _strip_youtube_noise("Adele - Hello (Official Music Video)") == "Adele - Hello"

    def test_strips_official_audio(self):
        assert _strip_youtube_noise("Hello (Official Audio)") == "Hello"

    def test_strips_hd_and_4k(self):
        assert _strip_youtube_noise("Song (HD)") == "Song"
        assert _strip_youtube_noise("Song [4K]") == "Song"

    def test_strips_lyrics_video(self):
        assert _strip_youtube_noise("Song (Lyrics Video)") == "Song"

    def test_strips_feat_bracket(self):
        assert _strip_youtube_noise("Song (feat. Other Artist)") == "Song"

    def test_preserves_legitimate_brackets(self):
        # "(pull me out of this)" should NOT be stripped -- not a noise pattern.
        assert _strip_youtube_noise("Delilah (pull me out of this)") == "Delilah (pull me out of this)"

    def test_no_change_when_clean(self):
        assert _strip_youtube_noise("Hello") == "Hello"
