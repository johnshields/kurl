# Platforms

Supported by backend (`models/schemas.py` PLATFORMS set):

| ID | Name | Brand colour | Icon | In UI |
|---|---|---|---|---|
| `spotify` | Spotify | `#1DB954` | SimpleIcons.spotify | yes |
| `appleMusic` | Apple | `#FA2D48` | SimpleIcons.applemusic | yes |
| `youtubeMusic` | YouTube | `#FF0000` | SimpleIcons.youtubemusic | yes |
| `deezer` | Deezer | `#A238FF` | (missing from simple_icons, use Icons.music_note) | no |
| `tidal` | Tidal | `#FFFFFF` | SimpleIcons.tidal | no |
| `amazonMusic` | Amazon | `#25D1DA` | SimpleIcons.amazonmusic | no |
| `pandora` | Pandora | `#224099` | SimpleIcons.pandora | no |

The backend accepts any of these as `target_platform` — keys match Odesli's `linksByPlatform`. UI currently only exposes the top three; add the rest to `app/lib/models/platform.dart` when ready.
