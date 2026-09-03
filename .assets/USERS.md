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
