# Platforms

Supported by backend (`app/constants.py::PLATFORMS`):

| ID | Name | Brand colour | Icon | API client |
|---|---|---|---|---|
| `spotify` | Spotify | `#1DB954` | SimpleIcons.spotify | OAuth client creds |
| `appleMusic` | Apple | `#FA2D48` | SimpleIcons.applemusic | JWT (ES256, requires Apple Developer Program) |
| `youtubeMusic` | YouTube | `#FF0000` | SimpleIcons.youtubemusic | oEmbed scrape only |
| `deezer` | Deezer | `#A238FF` | Icons.music_note | public, no auth |
| `tidal` | Tidal | `#FFFFFF` | SimpleIcons.tidal | OAuth client creds (v2 JSON:API) |
| `soundcloud` | SoundCloud | `#FF5500` | SimpleIcons.soundcloud | og scrape only |
| `amazonMusic` | Amazon | `#25D1DA` | SimpleIcons.amazonmusic | search URL only |
| `beatport` | Beatport | `#A8E00F` | SimpleIcons.beatport | search URL only |
| `bandcamp` | Bandcamp | `#629AA9` | SimpleIcons.bandcamp | og scrape only |

All 9 platforms exposed in the UI (`app/lib/models/platform.dart`). IDs match Odesli's `linksByPlatform` keys.

For platforms without an API client, kurler falls back to metadata scraping plus a search-page deep-link on the target.
