# Accounts plan (phase 1)

Basic account system: signup, login, preferred streaming platform, per-user kurl history. Backed by D1 (`env.kurl`, already bound in `wrangler.toml`). Follows/social features are phase 2, not scoped here.

## Stack confirmed from source

- API: Cloudflare Workers Python (Pyodide), custom router (`api/src/api/router.py:21` `@route(method, pattern)` decorator, not FastAPI)
- DB: D1 via thin wrapper `api/src/db/db.py` (`execute`, `fetch_all`), no ORM
- Existing table: `events` (`api/src/db/schemas/events.sql`), append-only analytics, no `user_id` column
- Auth today: single shared API key, `hmac.compare_digest` check in `api/src/api/middleware/auth.py:23`, binary (valid key or not) -- no concept of a per-user identity
- `PyJWT` is already a dependency (`api/pyproject.toml`) but only used for Apple MusicKit signing (`api/src/clients/platforms/apple.py:3`), not for sessions
- No password-hashing library in `api/pyproject.toml` (only `httpx`, `PyJWT`)
- No D1 migration runner found -- `events.sql` looks hand-applied, nothing in `.github/workflows/kurl.yml` runs it
- App: Flutter, `app/lib/services/api_service.dart` calls `POST /api/kurl` with no auth header of consequence (dead `X-API-Key` header was removed this session); no session/secure-storage package in `app/pubspec.yaml`
- Platform list already exists both sides: `app/lib/models/platform.dart:18` (`platforms`, used by the existing `PlatformPicker` widget) and `api/src/app/constants/platforms.py:3` (`PLATFORMS` set) -- reuse both for "preferred platform", do not add a third list

## Touch points

Backend (new files, following existing dir layout):
- `api/src/db/schemas/users.sql` -- new table
- `api/src/db/schemas/kurls.sql` -- new table (see open question below on reusing `events` instead)
- `api/src/db/queries/users.py` -- SQL strings, matching `api/src/db/queries/events.py` style
- `api/src/db/queries/kurls.py` -- SQL strings
- `api/src/models/user.py` -- row <-> dict mapping, matching `api/src/models/event.py` style
- `api/src/models/kurl_record.py` -- same, for a saved kurl row
- `api/src/api/controllers/auth_controller.py` -- signup/login/me logic, matching `api/src/api/controllers/events_controller.py` style
- `api/src/api/controllers/kurls_controller.py` -- record + list a user's kurls
- `api/src/api/routes/auth.py` -- thin HTTP layer, matching `api/src/api/routes/events.py` style
- `api/src/api/routes/kurls.py` -- thin HTTP layer
- `api/src/api/middleware/session_auth.py` -- new: verifies a per-user session token, separate from the existing shared-API-key `authenticate()` in `auth.py` (different mechanism, do not overload the existing function)

Backend (existing files to edit):
- `api/src/api/router.py:38-124` -- register new `@route(...)` blocks, mirroring the existing pattern exactly
- `api/src/api/middleware/auth.py:10-17` `PUBLIC_PATHS` -- add signup/login as public; `/api/auth/me` and `/api/kurls` need the new session check, not the existing one
- `api/src/entry.py:63-69` -- wire the new session check into the request pipeline alongside the existing `authenticate()`/`check_rate_limit()` calls

Frontend (existing placeholder files, built this session, meant for exactly this):
- `app/lib/app/routes/settings.dart` -- replace placeholder with login/signup form + preferred-platform picker (reuse `app/lib/widgets/shared/platform_picker.dart` as-is)
- `app/lib/app/routes/kurls.dart` -- replace placeholder with the user's kurl history list

Frontend (new files):
- `app/lib/services/auth_service.dart` -- signup/login/logout/me calls, matching `app/lib/services/api_service.dart` style
- `app/lib/models/user.dart`
- session token storage -- needs a new pubspec dependency, see open questions

## Decisions made (phase 1 built)

- **Kurl history schema**: new `kurls` table, not a reused/extended `events` column. Clean separation from bot-filtered analytics; user-owned, listable, deletable later.
- **Password hashing**: stdlib `hashlib.pbkdf2_hmac("sha256", ...)`, no new C-extension dependency (none available in Pyodide anyway). 120,000 iterations, well below OWASP's 600k -- a deliberate tradeoff for Workers' CPU-time budget, not yet benchmarked against real Workers limits (local dev was blocked by an unrelated Node/pywrangler issue all session -- benchmark this once unblocked). See `api/src/utils/password.py`.
- **Session tokens**: stateless JWT via the already-present `PyJWT`, signed with a new dedicated `SESSION_SECRET` (never reuses `KURL_API_KEY` -- mixing admin and user auth was exactly the bug fixed earlier this session). 30-day expiry, no revocation/denylist in phase 1 -- logout is client-side token discard only.
- **Usernames**: auto-generated on signup via `coolname` (pure Python, zero deps, added to `pyproject.toml`), two-word slugs like `classy-flounder`. User-changeable via `PATCH /api/auth/profile`, enforced unique (3-40 chars, letters/numbers/`-`/`_`).
- **Token storage (Flutter)**: `shared_preferences`. Works identically across web/iOS/Android with one package; not encrypted-at-rest on mobile (Keychain/Keystore would be), a deliberate simplicity tradeoff for a bearer token with a 30-day expiry, not a password.
- **Recording a kurl**: server-side, inside `services/urls.py`, best-effort (wrapped so a D1 write failure never affects the actual kurl response). Triggered only when the request carries a valid session `Authorization: Bearer <token>` header -- **kurling itself stays fully public and anonymous by default, exactly as before**. No session = no recording, no error, no behaviour change.
- **`wrap_route.py`**: left unused, matching the router's existing bare try/except style -- not adopted, to avoid an unrelated style change riding along with this feature.
- **Rate limiting**: reused the existing generic `check_rate_limit` as-is for phase 1. A dedicated stricter bucket for signup/login (brute-force protection) is a real gap, not yet built -- flagged as a followup, not blocking.
- **D1 schema application**: still no migration runner. `users.sql` and `kurls.sql` need the same manual `wrangler d1 execute --file=...` step `events.sql` presumably got. Not yet run against the real D1 database -- do this before deploying.

## API added

| Endpoint | Auth | Body / notes |
|---|---|---|
| `POST /api/auth/signup` | Public | `{email, password}` -> `{token, user}`. Username auto-generated. |
| `POST /api/auth/login` | Public | `{email, password}` -> `{token, user}` |
| `GET /api/auth/profile` | Session | Current user |
| `PATCH /api/auth/profile` | Session | `{username?, preferredPlatform?}` -- partial update, either or both |
| `GET /api/kurls` | Session | Signed-in user's last 100 kurls, newest first |
| `POST /api/kurl` | Public (unchanged) | Same as always; now also accepts an optional `Authorization: Bearer <token>` to opt into history recording |

Session auth = `Authorization: Bearer <JWT>`, verified by `api/src/api/middleware/session_auth.py` -- a completely separate mechanism from the existing `X-API-Key` admin check in `middleware/auth.py`. Error codes follow the existing `{status, code, message}` shape: `INVALID_EMAIL`, `WEAK_PASSWORD`, `EMAIL_TAKEN`, `INVALID_CREDENTIALS`, `INVALID_USERNAME`, `USERNAME_TAKEN`, `UNKNOWN_PLATFORM`, `NOT_FOUND`, `AUTH_REQUIRED`.

## Before deploying

- Set a `SESSION_SECRET` Worker secret, at least 32 bytes (`openssl rand -hex 32`). A short one triggers PyJWT's `InsecureKeyLengthWarning` in tests -- confirmed real, not a test-only artifact.
- Apply `api/src/db/schemas/users.sql` and `api/src/db/schemas/kurls.sql` to the D1 database by hand (same as `events.sql` was).
- `coolname` is a new `pyproject.toml` dependency -- confirm it bundles correctly on an actual deploy (pure Python, zero deps, so low risk, but nothing in this runtime has been "low risk and it just worked" so far this session).

## Frontend -- built

- `app/lib/services/auth_service.dart` -- signup/login/logout, token persistence (`shared_preferences`), profile get/update, kurl history fetch
- `app/lib/services/api_exception.dart` -- `ApiException` moved out of `api_service.dart` into its own file, to break the circular import with `auth_service.dart`
- `app/lib/models/user.dart`, `app/lib/models/kurl_history_item.dart`
- `app/lib/app/routes/settings.dart` -- login/signup form when logged out; profile view (email, editable username, `PlatformPicker` reuse for preferred platform, logout) when logged in
- `app/lib/app/routes/kurls.dart` -- history list; distinct empty states for "not signed in" vs "no kurls yet"
- `app/lib/services/api_service.dart` -- attaches `Authorization: Bearer <token>` when a session exists; still fully functional with no session, unchanged

Not done: no automated tests written for the new screens/services beyond the pre-existing smoke test. Not visually verified in a running app this session (`pywrangler dev` was blocked by the Node/wasm-flag issue noted earlier; web preview was declined) -- `flutter analyze` and `flutter test` are clean, but a real run-through hasn't happened yet.

## 2026-09-07: Sign in with Spotify

Goal: let a signed-in kurl user (existing email/password account) link their Spotify account. Phase A scope is identity only -- know which Spotify user this is. Reading their library / creating playlists is phase B, not scoped here.

### Stack confirmed from source

- Two separate origins: app served from `kurl.online` (Cloudflare Pages), api from `api.kurl.online` (Worker) -- `app/lib/app/config.dart:3`. A Spotify OAuth redirect must land on one of these; which one is an open question below.
- Spotify already has an app registered: `settings.SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` exist as Worker secrets (`api/src/clients/platforms/spotify.py:13-14`), currently used only for the **client_credentials** (app-only, no user) grant via `api/src/clients/platforms/_oauth.py:55-73`.
- `spotify.is_configured()` (`api/src/clients/platforms/spotify.py:29-36`) gates on a `SPOTIFY_API_ENABLED` flag that defaults to `false` (`api/src/app/config.py:62-63`) -- Spotify calls are currently a feature flag, off unless explicitly enabled. Reason not found in source; open question below.
- `_oauth.py`'s `TokenCache`/`fetch_client_credentials_token` (`api/src/clients/platforms/_oauth.py:18-73`) is client_credentials-only -- a user token flow (authorization_code grant + refresh_token) is a different grant type, needs new functions, not a reuse of `fetch_via_oauth` as-is.
- Session auth is stateless JWT, `Authorization: Bearer <token>`, verified by `api/src/api/middleware/session_auth.py`, separate from the shared-API-key check in `api/src/api/middleware/auth.py`. A new Spotify-callback route needs the same session-gated treatment as `/api/kurls/:uid` -- see `SESSION_GATED_PREFIXES` (`api/src/api/middleware/auth.py:30`).
- `users` table (`api/src/db/schemas/users.sql:4-12`) has no columns for a linked third-party account yet.
- Router uses a custom `@route(method, pattern)` decorator supporting `:param` path segments (`api/src/api/router.py:23-24`), same mechanism used for `DELETE /api/kurls/:uid`.
- Profile view where a "Connect Spotify" control would live: `app/lib/app/routes/settings.dart:443-460` (the existing "Preferred platform" `_card` block, same pattern).

### Touch points

Backend (new):
- `api/src/db/schemas/users.sql` or a new `spotify_accounts` table -- store `spotify_user_id`, `access_token`, `refresh_token`, `expires_at`, `scope`, linked to `users.uid`. Separate table is closer to the existing one-table-per-concern style (`kurls` is already split out from `users`).
- `api/src/db/queries/spotify_accounts.py` -- SQL strings, matching `api/src/db/queries/users.py` style.
- `api/src/clients/platforms/_oauth.py` -- add an authorization_code / refresh_token pair of functions alongside the existing `fetch_client_credentials_token`, or a new `_user_oauth.py` if mixing grant types in one file feels wrong (open question).
- `api/src/api/controllers/spotify_auth_controller.py` (or fold into `auth_controller.py`) -- build the Spotify authorize URL (with `state` tied to the signed-in session), handle the callback (exchange `code` for tokens, store them), disconnect (delete the row).
- `api/src/api/routes/spotify_auth.py` -- thin HTTP layer: `GET /api/auth/spotify/start`, `GET /api/auth/spotify/callback`, `DELETE /api/auth/spotify`.
- `api/src/api/router.py` -- register the three routes above, same pattern as the existing `@route(...)` blocks (e.g. `api/src/api/router.py:139-141` for the `DELETE /api/kurls/:uid` precedent).
- `api/src/api/middleware/auth.py` -- `/api/auth/spotify/start` and `/api/auth/spotify` (disconnect) need session gating like the rest of `/api/auth/*`; `/api/auth/spotify/callback` is hit directly by Spotify's redirect (no `Authorization` header available), so it must authenticate via the `state` param instead -- open question on exact mechanism below.

Backend (existing files to edit):
- `api/src/models/user.py` -- if storing on `users` directly rather than a new table, add the mapped field to `public_user()`.

Frontend (existing):
- `app/lib/app/routes/settings.dart:443-460` -- add a "Connect Spotify" / "Connected as {spotify display name}" row inside the existing Preferred platform `_card`, or a new `_card` block just for it.
- `app/lib/services/auth_service.dart` -- add calls for start/disconnect, matching the existing `_authedGet`/`_post` helpers.

Frontend (new):
- Nothing structurally new needed for the redirect itself -- Flutter web is same-origin already, no custom URL scheme required (unlike native iOS/Android, out of scope for phase A per the app's current web-first usage).

### Plan (once approved)

1. Register the redirect URI in the Spotify Developer Dashboard for this app (exact URI depends on the origin decision below).
2. Add `spotify_accounts` table + queries.
3. Add authorization_code + refresh_token functions to the Spotify OAuth client.
4. Add the three routes (start, callback, disconnect) + controller.
5. Add the "Connect Spotify" UI in `settings.dart` + `auth_service.dart` calls.
6. Apply the new schema to D1 by hand (same manual `wrangler d1 execute --file=...` step every other schema file has needed -- no migration runner exists, per the phase 1 note above).
7. Set the redirect URI + confirm scopes in the Spotify dashboard before first real test.

### Verify

- Manual: sign in to kurl, tap Connect Spotify, complete Spotify's consent screen, land back on kurl signed in with both, profile shows the linked Spotify identity.
- `GET /api/auth/profile` reflects the linked account.
- Disconnect removes the row and the UI reverts to "not connected".

### Risks / open questions

- **Redirect origin**: does Spotify redirect to `api.kurl.online/api/auth/spotify/callback` (Worker exchanges the code directly, then 302s the browser to `kurl.online`) or to a route on `kurl.online` that then calls the Worker? The Worker-first path is simpler and keeps `client_secret` server-side only; recommend that, but confirm before building.
- **Callback authentication**: the callback request comes from Spotify's redirect, not from the kurl app, so it carries no session `Authorization` header. The `state` param must encode (or look up) which kurl session initiated the flow -- exact mechanism (signed state token vs a short-lived server-side pending-auth row) not yet decided.
- **`SPOTIFY_API_ENABLED` reason**: currently defaults off; unclear from source whether this is because Spotify restricted API access for this app (Nov 2024 policy changes affected several endpoints for apps not in Extended Quota Mode) or an unrelated reason. Confirm the app's current Spotify dashboard quota mode before relying on it for user-facing login -- Development Mode caps at 25 authorized users (each must be added by email in the dashboard), which would silently block any user beyond the first 25.
- **Scopes**: phase A (identity only) needs no scopes beyond none/`user-read-email`. Do not request library/playlist scopes until phase B is actually scoped -- requesting more than needed also triggers Spotify's app review for restricted scopes.
- **Token refresh**: refresh tokens need a background or on-demand refresh path before expiry (typically 1 hour access token lifetime) -- where this runs (per-request lazy refresh vs a scheduled job) is not yet decided.
- **Existing client_credentials flow untouched**: this plan adds a second, separate OAuth grant type alongside the existing app-only one in `_oauth.py` -- must not disturb the existing catalog-search token cache (`TokenCache("Spotify")` in `spotify.py:6`).

### Decisions made (built)

- **Redirect origin**: Worker-first. Spotify redirects to `GET /api/auth/spotify/callback` on `api.kurl.online`; the Worker exchanges the code server-side (`client_secret` never leaves it), then 302s the browser to `settings.SPOTIFY_APP_REDIRECT_URL` (defaults to `https://kurl.online/settings`) with `?spotify=connected` or `?spotify=error`.
- **Callback authentication**: a dedicated short-lived (10 min) signed JWT `state` param, separate from session tokens -- `api/src/utils/oauth_state.py`, signed with the same `SESSION_SECRET`. No server-side pending-auth table needed; verified statelessly on callback.
- **Storage**: separate `spotify_accounts` table (`api/src/db/schemas/spotify_accounts.sql`), one row per `user_uid` (`UNIQUE`), upserted on reconnect. Tokens never exposed in API responses -- `public_spotify_account()` only returns `spotifyUserId`/`displayName`.
- **Scopes**: `user-read-email` only, per the identity-only phase A scope.
- **`SPOTIFY_API_ENABLED` flag**: removed entirely this session (separate from this feature) -- `is_configured()` now checks only client id/secret.
- **Token refresh**: not built yet -- tokens are stored (`access_token`, `refresh_token`, `expires_at`) but nothing refreshes them. Fine for phase A (identity only, tokens unused after linking); required before any phase B feature that calls the Spotify API as the user.

### Touch points (actual, as built)

Backend (new):
- `api/src/db/schemas/spotify_accounts.sql`, `api/src/db/queries/spotify_accounts.py`, `api/src/models/spotify_account.py`
- `api/src/utils/oauth_state.py` -- state token create/verify
- `api/src/clients/spotify_oauth_client.py` -- authorize URL, code exchange, refresh, `/v1/me` fetch
- `api/src/clients/platforms/_oauth.py` -- added `fetch_authorization_code_token`, `refresh_authorization_token` alongside the existing `fetch_client_credentials_token`
- `api/src/api/controllers/spotify_auth_controller.py`, `api/src/api/routes/spotify_auth.py`

Backend (edited):
- `api/src/app/constants/apis.py` -- `SPOTIFY_AUTHORIZE_URL`
- `api/src/app/config.py` -- `SPOTIFY_REDIRECT_URI`, `SPOTIFY_APP_REDIRECT_URL`
- `api/src/api/router.py` -- `GET /api/auth/spotify`, `GET /api/auth/spotify/start`, `GET /api/auth/spotify/callback`, `DELETE /api/auth/spotify`
- `api/src/api/middleware/auth.py` -- all four paths added to `PUBLIC_PATHS` (session-gated or, for `/callback`, state-gated -- not the shared admin key)
- `api/src/utils/http/response.py` -- added `redirect()` helper

Frontend (new):
- `app/lib/models/spotify_account.dart`

Frontend (edited):
- `app/lib/services/auth_service.dart` -- `getSpotifyStatus`, `startSpotifyAuth`, `disconnectSpotify`
- `app/lib/app/routes/settings.dart` -- Spotify card (Connect / Connected as X + Disconnect), same-tab redirect via `launchUrl(..., webOnlyWindowName: '_self')`, reads `?spotify=connected|error` on return to show a SnackBar

Tests: `api/src/__tests__/unit/test_oauth_state.py`, `api/src/__tests__/unit/test_spotify_auth_controller.py`. 232 backend tests pass, `ruff check` clean, `flutter analyze`/`flutter test` clean.

### Before deploying

- Register the redirect URI in the Spotify Developer Dashboard -- must exactly match whatever `SPOTIFY_REDIRECT_URI` is set to (e.g. `https://api.kurl.online/api/auth/spotify/callback`).
- Set Worker secrets: `SPOTIFY_REDIRECT_URI`, optionally `SPOTIFY_APP_REDIRECT_URL` if not using the `kurl.online/settings` default.
- Apply `api/src/db/schemas/spotify_accounts.sql` to D1 by hand (same manual step every other schema file has needed).
- **`users` table schema change**: `email` and `password_hash` are now nullable (a Spotify-only account has neither). If `users.sql` was already applied to the real D1 database, SQLite can't drop a `NOT NULL` constraint in place -- needs a manual rebuild:
  ```sql
  ALTER TABLE users RENAME TO users_old;
  -- then re-run the new CREATE TABLE from users.sql --
  INSERT INTO users SELECT id, uid, email, username, password_hash, preferred_platform, created_at FROM users_old;
  DROP TABLE users_old;
  ```
  Not yet run against the real database -- confirm this is safe against whatever's actually in there first.
- Confirm the app's Spotify dashboard quota mode before relying on this for real users -- Development Mode caps at 25 authorized users (each added by email in the dashboard). Not yet confirmed which mode this app is in.
- Not visually verified end-to-end (no real Spotify dashboard redirect URI registered yet, so the actual OAuth roundtrip hasn't been run) -- backend logic is unit-tested, frontend is `flutter analyze`/`flutter test` clean, but a real click-through hasn't happened.

### 2026-09-07 (later): redesigned as full sign-in, not just linking

Original build above only let an **already-signed-in** kurl user link Spotify (session required at `/start`). User clarified this was supposed to be full "Sign in with Spotify" from the start -- a visitor with no kurl account can tap it and get one, no email/password. Both modes now share one flow:

- **`/api/auth/spotify/start`** is no longer session-gated. `get_session_user_uid()` (never errors) checks for an existing session: present -> link mode, absent -> anonymous sign-in mode. Which mode is baked into the `state` param (see below), not into a second code path.
- **`oauth_state.py`** redesigned: `create_oauth_state(secret, user_uid=None)` / `verify_oauth_state(state, secret) -> (valid, user_uid_or_None)`. A present `user_uid` in the decoded state means link mode; absent means anonymous sign-in.
- **`handle_callback`**: link mode uses the state's `user_uid` directly. Anonymous mode calls `_resolve_user()`: look up `spotify_accounts` by `spotify_user_id` (returning user) -> else look up `users` by the email Spotify returned (matches an existing email/password account, links it) -> else create a brand-new account (`gen_uid`, `unique_username` reused from `auth_controller`, no password). Either way a session token is minted and appended to the redirect as `&token=<jwt>`, since the app has no other way to receive it.
- **`users` schema**: `email`/`password_hash` made nullable to allow Spotify-only accounts -- see the migration note above. `utils/password.py`'s `verify_password` now guards a `None` stored hash (returns `False`) instead of crashing.
- **`auth_controller.unique_username`**: unrelated existing username-generation retry loop, made public (was `_unique_username`) so the Spotify controller can reuse it rather than duplicating the collision-retry logic. Nothing about email/password signup or login changed -- both still work exactly as before; this only adds a second way to get an account.
- **Frontend**: `AuthService.startSpotifyAuth()` now sends the session token only if one exists (works signed-out too); new `AuthService.adoptSessionToken()` stores a token handed back via `?token=` on redirect. `SettingsScreen._loadProfile()` checks for that param before loading the profile. `_AuthForm` (the actual sign-in/signup screen) gained a "Continue with Spotify" button above the email/password fields, with an "or" divider.

Tests rewritten for the new signatures/flow (`test_oauth_state.py`, `test_spotify_auth_controller.py`). 238 backend tests pass, `ruff check` clean, `flutter analyze`/`flutter test` clean.

## 2026-09-07: Forgot password + change password

Email/password accounts can now reset a forgotten password via emailed link, and a signed-in user can change their password directly from Settings.

### Decisions made (built)

- **Email delivery**: Cloudflare Email Service (`env.EMAIL.send()` via the `send_email` binding) -- user confirmed they're already on the Workers Paid plan, which Email Sending to arbitrary recipients requires (not available on Free). `api/src/clients/email.py` follows the exact same module-level-binding pattern as `clients/cache.py` (`init_email()` called from `entry.py`, alongside `cache.init_kv()`), avoiding threading the binding through every controller/route signature.
- **Reset token**: stateless signed JWT (`utils/password_reset.py`), no DB table -- same rationale as `oauth_state.py`. Embeds a fingerprint (`sha256(password_hash)[:16]`) of the account's password_hash *at issue time*; on reset, the fingerprint is compared against the *current* password_hash, so a token becomes invalid the instant the password actually changes -- gives single-use-like behaviour for free, no separate used-token tracking. Also works for an account with no password yet (Spotify-only) -- fingerprints a `None` hash consistently, so the same link doubles as "set your first password."
- **Enumeration**: `POST /api/auth/forgot-password` always returns the same success message regardless of whether the email has an account -- only sends an email when one exists.
- **Change password (signed in)**: reused the existing `PATCH /api/auth/profile` partial-update endpoint rather than a new route -- `update_profile()` now also accepts `password`, same session-gated mechanism as username/preferredPlatform.
- **Reset link target**: `https://kurl.online/settings?reset=<token>` -- new `APP_BASE_URL` constant (`app/constants/network.py`), separate from the Spotify-specific `SPOTIFY_APP_REDIRECT_URL`.

### Touch points (as built)

Backend (new):
- `api/src/clients/email.py`, `api/src/utils/password_reset.py`
- `api/src/__tests__/unit/test_password_reset.py`

Backend (edited):
- `api/src/db/schemas/users.sql` already nullable from the Spotify work; `api/src/db/queries/users.py` -- `UPDATE_PASSWORD`
- `api/src/api/controllers/auth_controller.py` -- `forgot_password`, `reset_password`, `update_profile` now also handles `password`
- `api/src/api/routes/auth.py`, `api/src/api/router.py` -- `POST /api/auth/forgot-password`, `POST /api/auth/reset-password`
- `api/src/api/middleware/auth.py` -- both new paths added to `PUBLIC_PATHS` (no session/API key -- forgot-password is pre-login, reset-password authenticates via the token itself)
- `api/src/app/constants/network.py` -- `APP_BASE_URL`, `EMAIL_FROM`
- `api/src/entry.py` -- `email.init_email(...)` wired in alongside the KV cache init
- `api/wrangler.toml` -- `[[send_email]] name = "EMAIL"`
- `api/src/__tests__/unit/test_auth_controller.py` -- new `TestForgotPassword`, `TestResetPassword`, password cases added to `TestUpdateProfile`

Frontend (new):
- `_ForgotPasswordDialog`, `_ResetPasswordForm` in `app/lib/app/routes/settings.dart`

Frontend (edited):
- `app/lib/services/auth_service.dart` -- `forgotPassword`, `resetPassword`, `updateProfile(password:)`
- `app/lib/app/routes/settings.dart` -- "Forgot password?" link (sign-in mode only) opening the dialog; `?reset=` query param shows `_ResetPasswordForm` instead of the normal sign-in/profile view, clears the param via `updateUrlState()` on success; new "Change password" card in the profile view between Username and Spotify

253 backend tests pass (added 15), `ruff check` clean, `flutter analyze`/`flutter test` clean.

### Before deploying

- Onboard the sending domain: `npx wrangler email sending enable kurl.online` (adds SPF/DKIM DNS records -- since kurl.online is already on Cloudflare DNS this should be quick, but hasn't been run yet).
- Confirm `EMAIL_FROM` (`noreply@kurl.online`) doesn't need a specific mailbox to exist -- Email Sending sends *from* any address on an onboarded domain, no inbox required unless also using Email Routing.
- **Real unknown, flagged honestly**: calling `env.EMAIL.send()` from Python Workers hasn't been done anywhere in this codebase before. The kwargs -> JS-object calling convention is proven for `_kv.put(key, value, expirationTtl=seconds)` in `clients/cache.py`, and `clients/email.py`'s `send()` follows that exact same shape, but it's reasoned from precedent, not verified against the real `send_email` binding. If it doesn't work as expected, check `wrangler tail` after a real `forgot-password` call -- `email.send()` already catches and logs any exception rather than raising, so a failure there won't break the request, just silently not send the email.
- Not visually verified end-to-end (no real email has been sent) -- backend logic is unit-tested, frontend is `flutter analyze`/`flutter test` clean, but a real click-through (request reset -> receive email -> click link -> set password) hasn't happened yet.

## 2026-09-07 (later): Email verification on signup

Soft verification -- user confirmed nothing should be blocked. Signup sends a verification email; unverified accounts can still log in, kurl, and do everything else. Just a badge + resend button until clicked.

### Decisions made (built)

- **Token**: stateless signed JWT (`utils/email_verification.py`), 24h expiry, no fingerprint mechanism like `password_reset.py` -- re-verifying an already-verified account is a harmless no-op, so there's nothing that needs to self-invalidate.
- **Schema**: `users.email_verified_at TEXT` (nullable, `NULL` = unverified) added via plain `ALTER TABLE ... ADD COLUMN` -- unlike the earlier nullable-column change, SQLite allows adding a column without a table rebuild, so no destructive migration needed this time.
- **Verify link**: `https://kurl.online/settings?verify=<token>`. Calling `verify-email` needs no session (someone might click it on a different device) -- if the browser happens to be signed in as that account, the profile view picks up the change on next load.
- **Resend**: session-gated (`POST /api/auth/resend-verification`, uses the caller's own session, not a token) -- short-circuits with a success response if already verified, otherwise re-sends via the same `_send_verification_email` helper signup uses.

### Touch points (as built)

Backend (new):
- `api/src/utils/email_verification.py`
- `api/src/__tests__/unit/test_email_verification.py`

Backend (edited):
- `api/src/db/schemas/users.sql` -- `email_verified_at` column (fresh DBs only; live D1 needs the `ALTER TABLE` below)
- `api/src/db/queries/users.py` -- `UPDATE_EMAIL_VERIFIED`
- `api/src/models/user.py` -- `public_user()` now returns `emailVerified`
- `api/src/api/controllers/auth_controller.py` -- `_send_verification_email` (shared by signup and resend), `verify_email`, `resend_verification`; `signup()` now sends the email and returns `emailVerified: false`
- `api/src/api/routes/auth.py`, `api/src/api/router.py` -- `POST /api/auth/verify-email` (public), `POST /api/auth/resend-verification` (session-gated)
- `api/src/api/middleware/auth.py` -- both new paths added to `PUBLIC_PATHS`
- `api/src/__tests__/unit/test_auth_controller.py` -- `TestVerifyEmail`, `TestResendVerification`

Frontend (edited):
- `app/lib/models/user.dart` -- `emailVerified` field
- `app/lib/services/auth_service.dart` -- `verifyEmail`, `resendVerification`
- `app/lib/app/routes/settings.dart` -- `SettingsScreen._loadProfile()` calls `verifyEmail` when `?verify=` is present (best-effort, falls through either way); profile view shows an "Email not verified" row with a Resend button under the email when `!emailVerified`; a snackbar + `updateUrlState()` on return confirms success/failure and clears the query param, mirroring the existing Spotify-return-message pattern

265 backend tests pass (added 12), `ruff check` clean, `flutter analyze`/`flutter test` clean.

### Before deploying

- Apply the schema change to the live D1 database by hand: `ALTER TABLE users ADD COLUMN email_verified_at TEXT;` (safe, additive -- no table rebuild, no data loss, unlike the earlier nullable-column migration).
- Everything else (Email Sending domain, `send_email` binding) is already set up from the forgot-password work above -- no new secrets or bindings needed.
- Not visually verified end-to-end -- same caveat as forgot-password: unit-tested and analyze-clean, but no real signup-then-click-the-link run has happened yet.
