# Backlog

Prioritised list of improvements, grouped by effort. Not a commitment — a menu.

## Recently shipped

- **Auto-detect source platform** — URL is parsed client-side on paste; a "From Spotify — pick a target" chip appears above the picker so users don't have to think about the source
- **Short-link resolver** — `spotify.link` and `dzr.page.link` URLs are now resolved server-side (HTTP redirect for Deezer, `og:url` or meta refresh for Spotify) before parsing
- **ISRC cache layer** — Redis namespace `isrc:{platform}:{entity_type}:{id}` caches ISRC + title + artist, so kurling the same source track to multiple targets only calls the source API once

## Quick wins (each < 1 hour)

1. **Enter key submits** — currently the button has to be tapped even when the keyboard is up
2. **Kurl history** — last 5-10 results stored in SQLite, shown as chips below the result card ("Recent: Fred again.. → Spotify")
3. **Haptic feedback** on success/error (mobile only)
4. **Select-all on focus** — tapping the field highlights existing text, ready to overwrite
5. **Paste-and-submit** — if a URL is pasted into an empty field and a platform is already picked, auto-kurl

## Medium lifts (1-3 hours)

6. **Rate limiting** — `slowapi` middleware, per-IP. Free-tier protection
7. **Pre-commit hooks** — ruff check + pytest -q before every commit (using `pre-commit`)
8. **Retry + backoff on platform API 429s** — currently only Odesli has this. Spotify/Tidal need it too
9. **Negative-result cache** — 15-min TTL for misses so broken matches don't get hammered
10. **Mobile widget tests** — the marquee, picker, and result card have no tests yet

## Bigger bets (4-8 hours)

11. **Sentry / error tracking** — backend + mobile. Visibility into what breaks in production
12. **Analytics endpoint** — `/api/stats` showing resolution success rate by `via` path (isrc vs search_api vs Odesli vs 404). Data to decide where to invest next
13. **Browser extension** — right-click any music link → "kurl to Spotify". Distribution play
14. **Shareable short URL** — `kurl.sh/abc` resolves server-side and redirects directly, skipping the app
15. **Metadata cache layer** — cache scraped metadata separately from kurl results. Popular YouTube videos get resolved faster

## Product-level

16. **Favourites** — persistent platform pref per friend. Phase 2 of the roadmap
17. **Onboarding screen** — "what is kurl?" three-slide intro on first launch
18. **Tablet / web landscape layout** — responsive breakpoints rather than just scaling up
19. **Dark/light theme toggle** — currently hardcoded dark
20. **Localisation** — UK/US English strings externalised, ready for more

## Next three to do

If picking three high-impact items with contained scope:

- **#1 Enter key submits** — trivial UX fix that makes the app feel native
- **#8 Retry + backoff on platform 429s** — matches the Odesli client's resilience; one less class of flake
- **#10 Mobile widget tests** — catches regressions in the marquee/picker/result card that visual inspection missed today
