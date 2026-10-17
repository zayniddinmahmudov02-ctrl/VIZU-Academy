#!/usr/bin/env bash
# Frontend deploy without serving a half-built .next.
#
# `next build` empties and rewrites its output directory, so building into
# the directory `next start` is serving from yields missing BUILD_ID /
# client reference manifests / pages/500.html and HTTP 500s until the
# service is restarted. Instead this script alternates between two build
# slots (.next-a / .next-b):
#
#   1. build into the slot that is NOT live (the live one keeps serving),
#   2. verify the build output is complete,
#   3. point .deploy/active.env at the new slot and restart the service once,
#   4. health-check; on failure switch back to the previous slot.
#
# The slot name is compiled into the server bundles (distDir), so the
# service must start with the same NEXT_DIST_DIR it was built with — that is
# what the systemd EnvironmentFile provides (one-time setup:
# docs/deploy-frontend.md).
#
# Run from anywhere, as the user that owns the checkout (sudo is only used
# for systemctl). Does NOT git pull, touch .env files or node_modules.
# Options:
#   --install   run `npm ci` first. This rewrites node_modules under the
#               running server: only use it when package-lock.json changed,
#               and expect errors until the restart.
set -euo pipefail

FRONTEND_DIR="${FRONTEND_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SERVICE="${SERVICE:-vizu-frontend}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:3000/login}"
SYSTEMCTL="${SYSTEMCTL:-sudo systemctl}"
STATE_DIR="$FRONTEND_DIR/.deploy"
ACTIVE_ENV="$STATE_DIR/active.env"
REQUIRED_ROUTES=(admin/lessons admin/levels admin/modules "(dashboard)/lessons/[lessonId]/[section]")

install=0
for arg in "$@"; do
  case "$arg" in
    --install) install=1 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

cd "$FRONTEND_DIR"
mkdir -p "$STATE_DIR"

# One-time setup must be in place, otherwise the service would keep
# serving .next and never see the new slot.
# (no `grep -q` here: it exits on the first match, systemctl gets SIGPIPE and
# with pipefail the check fails at random)
if ! $SYSTEMCTL cat "$SERVICE" 2>/dev/null | grep -F "$ACTIVE_ENV" >/dev/null; then
  echo "ERROR: $SERVICE has no EnvironmentFile=-$ACTIVE_ENV (see docs/deploy-frontend.md, one-time setup)." >&2
  exit 1
fi

current=""
[ -f "$ACTIVE_ENV" ] && current="$(sed -n 's/^NEXT_DIST_DIR=//p' "$ACTIVE_ENV")"
if [ "$current" = ".next-a" ]; then slot=".next-b"; else slot=".next-a"; fi
deploy_id="$(git -C "$FRONTEND_DIR" rev-parse --short HEAD)-$(date +%Y%m%d%H%M%S)"

echo "live slot: ${current:-.next}  ->  building $slot (deployment $deploy_id)"

if [ "$install" = 1 ]; then
  npm ci --no-audit --no-fund
fi

rm -rf "$slot"
# tsconfig includes the generated route types of every slot; the live
# slot's still name pages this commit may have removed and would fail the
# type check. They are type-check only (the running server never reads
# them), so dropping them leaves the live slot and the rollback intact.
for d in .next .next-a .next-b; do rm -rf "$d/types" "$d/dev/types"; done
NEXT_DIST_DIR="$slot" NEXT_DEPLOYMENT_ID="$deploy_id" npm run build

missing=0
for f in BUILD_ID required-server-files.json server/middleware-manifest.json server/app-paths-manifest.json server/pages/500.html; do
  [ -e "$slot/$f" ] || { echo "missing $slot/$f" >&2; missing=1; }
done
for r in "${REQUIRED_ROUTES[@]}"; do
  [ -e "$slot/server/app/$r/page_client-reference-manifest.js" ] || { echo "missing client reference manifest for /$r" >&2; missing=1; }
done
if [ "$missing" = 1 ]; then
  echo "ERROR: build output incomplete — live slot ${current:-.next} untouched." >&2
  exit 1
fi

[ -f "$ACTIVE_ENV" ] && cp "$ACTIVE_ENV" "$ACTIVE_ENV.prev"
printf 'NEXT_DIST_DIR=%s\nNEXT_DEPLOYMENT_ID=%s\n' "$slot" "$deploy_id" > "$ACTIVE_ENV.tmp"
mv "$ACTIVE_ENV.tmp" "$ACTIVE_ENV"

$SYSTEMCTL restart "$SERVICE"

healthy=0
for _ in $(seq 1 30); do
  if curl -fsS -o /dev/null --max-time 5 "$HEALTH_URL"; then healthy=1; break; fi
  sleep 1
done

if [ "$healthy" != 1 ]; then
  echo "ERROR: $HEALTH_URL not healthy after restart — rolling back to ${current:-.next}." >&2
  if [ -f "$ACTIVE_ENV.prev" ]; then mv "$ACTIVE_ENV.prev" "$ACTIVE_ENV"; else rm -f "$ACTIVE_ENV"; fi
  $SYSTEMCTL restart "$SERVICE"
  for _ in $(seq 1 30); do
    if curl -fsS -o /dev/null --max-time 5 "$HEALTH_URL"; then
      echo "rolled back: $SERVICE serves ${current:-.next} again." >&2
      exit 1
    fi
    sleep 1
  done
  echo "ERROR: rollback is not healthy either — check: journalctl -u $SERVICE -n 100" >&2
  exit 1
fi

echo "OK: $SERVICE serves $slot (deployment $deploy_id). Previous slot ${current:-.next} kept for rollback."
