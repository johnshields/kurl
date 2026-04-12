# References

## Odesli (song.link)

The API kurl uses in phase 1 to resolve cross-platform links.

- API base: `https://api.song.link/v1-alpha.1/links`
- Pass a streaming URL, get back `linksByPlatform` with URLs for every platform the track exists on
- Also returns `entitiesByUniqueId` with track metadata (title, artist, ISRC)
- Free tier works without an API key, has rate limits
- Matching is done via ISRC codes internally
- Docs: https://odesli.co

## ISRC (building our own resolver later)

Every properly distributed track gets the same ISRC across all platforms. If we ever move off Odesli, this is how:

| Platform | Get ISRC from link | Search by ISRC | API access |
|---|---|---|---|
| Spotify | Yes (`external_ids.isrc`) | Yes (`isrc:` filter) | Free, OAuth client credentials |
| Apple Music | Yes (track metadata) | Yes (batch up to 25) | Free, Apple Developer account |
| Deezer | Yes (track object) | Yes (undocumented `/track/isrc:{code}`) | Free, no auth |
| Tidal | Yes (track metadata) | Yes | Developer portal |
| YouTube Music | No | No public ISRC search | No official music API |
| Amazon Music | No | No | Closed |
| Pandora | No | No | Closed |

For YouTube/Amazon/Pandora, fallback to fuzzy matching on artist + track name.

Useful reference: https://medium.com/@leemartin/how-to-match-tracks-between-spotify-and-apple-music-2d6b6159957e

## SubmitHub comparison

SubmitHub's "Links" feature is a different thing — it's a landing page builder where artists manually add their own platform links. Not auto-resolution. More like Linktree for music than a URL converter.

kurl automates the resolution (paste one link, get the equivalent on another platform). Different use case entirely.

## Other smart link services

- **Songwhip** — shut down in 2023, was similar to Odesli
- **Musicfetch** (musicfetch.io) — paid API for cross-platform matching
- **Linkfire, ToneDen, Feature.fm** — marketing-focused smart link builders, not real-time converters
