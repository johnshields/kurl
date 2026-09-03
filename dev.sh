#!/usr/bin/env bash
# Run kurl api (pywrangler dev) and app (flutter web) together for local dev.
set -e

root="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
    kill $(jobs -p) 2>/dev/null
}
trap cleanup EXIT INT TERM

(cd "$root/api" && PATH="/opt/homebrew/opt/node@24/bin:$PATH" pywrangler dev 2>&1 | sed 's/^/[api] /') &
(cd "$root/app" && flutter run -d chrome --web-port 5173 2>&1 | sed 's/^/[app] /') &

wait
