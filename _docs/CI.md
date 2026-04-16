# CI

GitHub Actions pipeline: `.github/workflows/kurl.yml`. Triggers on push/PR to `main`, concurrency-grouped so only the latest ref runs.

## Jobs

Three jobs chained via `needs:`. Failure in an earlier job cancels the later ones.

### 1. `lint`
Fast-fail on style issues before anything else runs.
- `ruff check .` — catches errors, unused imports, bugbear anti-patterns, import ordering
- `ruff format --check .` — enforces formatting without writing

Runs on Python 3.12. Config: `backend/ruff.toml`.

### 2. `test`
Matrix build over Python **3.11** and **3.12**. Runs the full pytest suite with coverage.
- `pytest --cov=. --cov-report=xml -q`
- Uploads `coverage.xml` to Codecov (3.12 only) with `fail_ci_if_error: false`
- `fail-fast: false` — one version failing doesn't cancel the other

### 3. `smoke`
End-to-end sanity check against a live backend. Uses the `kurl_env` GitHub environment for secrets.

1. Boot `uvicorn main:app` in the background
2. `curl -fsS /api/healthz` — liveness
3. `curl -fsS /api/readyz` — readiness with all configured clients probed
4. Stop uvicorn (runs on `if: always()` so logs upload even on failure)
5. Upload `uvicorn.log` artifact on failure

`/readyz` returns 503 if any **configured** client is unreachable. Unconfigured clients (e.g. Apple without creds) return `"skipped"` and don't fail the check.

## Environment and secrets

All backend secrets live on the `kurl_env` GitHub environment — Settings → Environments → kurl_env.

| Secret | Required | Effect if missing |
|---|---|---|
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | yes | Spotify shows `skipped` in `/readyz` |
| `TIDAL_CLIENT_ID` / `TIDAL_CLIENT_SECRET` | yes | Tidal shows `skipped` |
| `APPLE_TEAM_ID` / `APPLE_KEY_ID` / `APPLE_PRIVATE_KEY` | no | Apple shows `skipped` (expected — not enrolled yet) |
| `ODESLI_API_KEY` | no | Falls back to free-tier Odesli |
| `CODECOV_TOKEN` | no | Coverage upload may flake but won't fail CI |

### Setting secrets via gh CLI
```bash
gh secret set SPOTIFY_CLIENT_ID --env kurl_env --body "..."
gh secret set APPLE_PRIVATE_KEY --env kurl_env < apple_key.p8
gh secret list --env kurl_env
```

### Creating the environment
```bash
gh api --method PUT repos/<owner>/kurl/environments/kurl_env
```

## Running CI checks locally

Everything CI does can run locally:

```bash
cd backend
source venv/bin/activate

ruff check .             # = job 1
ruff format --check .
pytest -q                # = job 2
pytest --cov             # with coverage
uvicorn main:app &       # = job 3
curl -fsS localhost:8000/api/healthz
curl -fsS localhost:8000/api/readyz | python -m json.tool
```
