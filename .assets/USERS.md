# Accounts

Optional account system: email/password or sign in with Spotify/Deezer/SoundCloud, preferred platform, kurl history. Kurling itself stays fully anonymous by default. An account only adds history + a preferred platform.

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
| `PATCH /api/auth/profile` | Session | `{username?, preferredPlatform?, password?}` |
| `GET/DELETE /api/auth/spotify` | Session | Status / disconnect |
| `GET /api/auth/spotify/start` | Optional | Session present -> link mode, absent -> sign-in |
| `GET /api/auth/spotify/callback` | State token | Spotify's own redirect |
| `GET/DELETE /api/auth/deezer` | Session | Same shape as Spotify. **Disabled in the app UI**: Deezer closed new app registration |
| `GET /api/auth/deezer/start` | Optional | |
| `GET /api/auth/deezer/callback` | State token | |
| `GET/DELETE /api/auth/soundcloud` | Session | Same shape as Spotify |
| `GET /api/auth/soundcloud/start` | Optional | |
| `GET /api/auth/soundcloud/callback` | State token | |
| `GET /api/kurls` | Session | Last 100, newest first |
| `DELETE /api/kurls/:uid` | Session | |

## Sign in with a platform

One flow, two modes, shared across all three providers: an existing session on `/start` means link mode (tie the platform to that account), no session means anonymous sign-in (find or create an account for that identity). Mode is baked into the `state` param, not a second code path.

State/CSRF token: `utils/oauth_state.py`, stateless signed JWT, 10 min expiry, signed with `SESSION_SECRET`. Optional `user_uid` claim = link mode. Optional `verifier` claim carries a PKCE code verifier for providers that need one back at token exchange (SoundCloud).

Callback success mints a session token and appends it to the app redirect as `&token=`, since there's no other way to hand it to the app.

| | Spotify | Deezer | SoundCloud |
|---|---|---|---|
| Grant | authorization_code | authorization_code | authorization_code + PKCE |
| Token exchange | POST, HTTP Basic auth, JSON response | GET, query-string response | POST, `client_id`/`secret` in body, JSON response |
| `state` param | Standard, echoed back | **Not echoed back**: embedded in the `redirect_uri` query string instead | Standard, echoed back |
| Refresh token | Yes | No (non-expiring `offline_access` token instead) | Yes |
| Email available | Yes | Yes | **No**: match by provider user id only |

Deezer and SoundCloud's OAuth clients don't reuse `clients/platforms/_oauth.py`'s shared token-exchange helper (built for Spotify's dialect). Each is a standalone client matching its own provider's contract.

## Schema

| Table | Key columns |
|---|---|
| `users` | `uid`, `email` (nullable), `username`, `password_hash` (nullable), `preferred_platform`, `email_verified_at` |
| `kurls` | `uid`, `user_uid`, `source_url`, `target_url`, `platform`, `via`, `title`, `artist` |
| `spotify_accounts` | `user_uid` (unique), `spotify_user_id`, `display_name`, `access_token`, `refresh_token`, `expires_at`, `scope` |
| `deezer_accounts` | `user_uid` (unique), `deezer_user_id`, `display_name`, `access_token`, `expires_at` (nullable) |
| `soundcloud_accounts` | `user_uid` (unique), `soundcloud_user_id`, `display_name`, `access_token`, `refresh_token`, `expires_at`, `scope` |

No migration runner. Schema files are applied to D1 by hand (`wrangler d1 execute --file=...`).

## Known gaps

- Deezer sign-in disabled in the app UI (registration closed). Backend stays live, ready to re-enable once a `DEEZER_APP_ID`/`SECRET` exist.
- Not confirmed whether kurl's existing SoundCloud app has the sign-in grant enabled, distinct from the catalog-search client_credentials grant it already uses.
- No token refresh implemented for any provider (tokens stored, unused after linking, identity only, no library/playlist scopes).
- No rate limiting specific to signup/login beyond the generic per-IP limiter.
