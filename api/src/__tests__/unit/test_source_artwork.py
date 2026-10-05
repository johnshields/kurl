"""
Tests for the extract_artwork helpers on the source platform clients.
"""

from clients.platforms import apple, soundcloud, spotify


class TestSpotify:
    def test_track_reads_the_album_images(self):
        assert spotify.extract_artwork({"album": {"images": [{"url": "big"}, {"url": "small"}]}}) == "big"

    def test_album_reads_its_own_images(self):
        assert spotify.extract_artwork({"images": [{"url": "cover"}]}) == "cover"

    def test_no_images(self):
        assert spotify.extract_artwork({"album": {"images": []}}) is None


class TestApple:
    def test_fills_the_size_template(self):
        entity = {"attributes": {"artwork": {"url": "https://a/{w}x{h}bb.jpg"}}}
        assert apple.extract_artwork(entity) == "https://a/600x600bb.jpg"

    def test_no_artwork(self):
        assert apple.extract_artwork({"attributes": {}}) is None


class TestSoundCloud:
    def test_upgrades_the_size(self):
        assert soundcloud.extract_artwork({"artwork_url": "https://s/x-large.jpg"}) == "https://s/x-t500x500.jpg"

    def test_no_artwork(self):
        assert soundcloud.extract_artwork({"artwork_url": None}) is None
