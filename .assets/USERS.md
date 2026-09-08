# Accounts

Optional account system: email/password or sign in with Spotify/SoundCloud/YouTube, preferred platform, kurl history. Kurling itself stays fully anonymous by default. An account only adds history + a preferred platform.

Deezer sign-in was removed (Deezer closed new app registration, so it could never go live). Recoverable from git history if that changes.

## Auth

Session: stateless JWT, `Authorization: Bearer <token>`, signed with `SESSION_SECRET`, 30 days, no revocation (logout is client-side discard). Separate from the shared `X-API-Key` admin check in `middleware/auth.py`.

Password hashing: `hashlib.pbkdf2_hmac("sha256", ...)`, 120,000 iterations.

## Endpoints

| Endpoint | Auth | Notes |
|---|---|---|
| `POST /api/auth/signup` | Public | `{email, password}` -> `{token, user}`. Username auto-generated (`coolname`). |
| `POST /api/auth/login` | Public | `{email, password}` -> `{token, user}` |
| `POST /api/auth/forgot-password` | Public | Always returns success, regardless of whether the email exists |
| `POST /api/auth/reset-password` | Token | `{token, password}` |
| `POST /api/auth/verify-email` | Public | `{token}` |
| `POST /api/auth/resend-verification` | Session | |
| `GET /api/auth/profile` | Session | |
| `PATCH /api/auth/profile` | Session | `{email?, username?, preferredPlatform?, password?}`. `email` only settable once (accounts with no email, e.g. SoundCloud sign-in) |
| `GET/DELETE /api/auth/spotify` | Session | Status / disconnect |
| `GET /api/auth/spotify/start` | Optional | Session present -> link mode, absent -> sign-in |
| `GET /api/auth/spotify/callback` | State token | Spotify's own redirect |
| `GET/DELETE /api/auth/soundcloud` | Session | Same shape as Spotify |
| `GET /api/auth/soundcloud/start` | Optional | |
| `GET /api/auth/soundcloud/callback` | State token | |
| `GET/DELETE /api/auth/google` | Session | Same shape as Spotify. Button labelled "YouTube" |
| `GET /api/auth/google/start` | Optional | |
| `GET /api/auth/google/callback` | State token | |
| `GET /api/kurls` | Session | Last 100, newest first |
| `DELETE /api/kurls/:uid` | Session | |

## Sign in with a platform

One flow, two modes, shared across all three providers: an existing session on `/start` means link mode (tie the platform to that account), no session means anonymous sign-in (find or create an account for that identity). Mode is baked into the `state` param, not a second code path.

State/CSRF token: `utils/oauth_state.py`, stateless signed JWT, 10 min expiry, signed with `SESSION_SECRET`. Optional `user_uid` claim = link mode. Optional `verifier` claim carries a PKCE code verifier for providers that need one back at token exchange (SoundCloud).

Callback success mints a session token and appends it to the app redirect as `&token=`, since there's no other way to hand it to the app.

| | Spotify | SoundCloud | Google (YouTube) |
|---|---|---|---|
| Grant | authorization_code | authorization_code + PKCE | authorization_code |
| Token exchange | POST, HTTP Basic auth, JSON response | POST, `client_id`/`secret` in body, JSON response | POST, `client_id`/`secret` in body, JSON response |
| `state` param | Standard, echoed back | Standard, echoed back | Standard, echoed back |
| Refresh token | Yes | Yes | Only on first consent (or forced re-consent) |
| Email available | Yes | **No**: match by provider user id only | Yes |

SoundCloud and Google's OAuth clients don't reuse `clients/platforms/_oauth.py`'s shared token-exchange helper (built for Spotify's Basic-auth dialect). Each is a standalone client matching its own provider's contract.

Google's identity client (`clients/google_oauth_client.py`, `GOOGLE_CLIENT_ID`/`SECRET`) is entirely separate from `settings.YOUTUBE_API_KEY`, an unrelated Data API v3 key used for catalog search.

`access_token`/`refresh_token` are encrypted before being written (`utils/token_crypto.py`, AES-256-GCM via `crypto.subtle`, key in `TOKEN_ENCRYPTION_KEY`). Encryption fails closed: no key configured, or the FFI call fails, and the row gets an empty string instead of plaintext. Untested outside a real deploy -- `crypto.subtle` doesn't exist under pytest's plain CPython.

## Schema

| Table | Key columns |
|---|---|
| `users` | `uid`, `email` (nullable), `username`, `password_hash` (nullable), `preferred_platform`, `email_verified_at` |
| `kurls` | `uid`, `user_uid`, `source_url`, `target_url`, `platform`, `via`, `title`, `artist` |
| `spotify_accounts` | `user_uid` (unique), `spotify_user_id`, `display_name`, `access_token`, `refresh_token`, `expires_at`, `scope` |
| `soundcloud_accounts` | `user_uid` (unique), `soundcloud_user_id`, `display_name`, `access_token`, `refresh_token`, `expires_at`, `scope` |
| `google_accounts` | `user_uid` (unique), `google_user_id`, `display_name`, `access_token`, `refresh_token` (nullable), `expires_at`, `scope` |

No migration runner. Schema files are applied to D1 by hand (`wrangler d1 execute --file=...`).

## Known gaps

- No token refresh implemented for any provider (tokens stored, unused after linking, identity only, no library/playlist scopes).
- No rate limiting specific to signup/login beyond the generic per-IP limiter.
