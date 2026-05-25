#!/usr/bin/env bash
# Tails the global bus, filters tier=="alert", shells to apprise.
set -uo pipefail

if [ "${CLAUDE_PLUGIN_OPTION_APPRISE_ENABLED:-true}" != "true" ]; then
  echo "broadcastr: apprise disabled by config" >&2
  exit 0
fi

if ! command -v apprise >/dev/null 2>&1; then
  echo "broadcastr: apprise CLI not installed; alert gateway exiting" >&2
  exit 0
fi

GLOBAL_HOME="${BROADCASTR_HOME:-$HOME/.claude/broadcastr}"
BUS="$GLOBAL_HOME/events.jsonl"
TAG="${CLAUDE_PLUGIN_OPTION_APPRISE_TAG:-broadcastr}"

mkdir -p "$GLOBAL_HOME"
touch "$BUS"

STARTUP="$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"

cleanup() { pkill -P $$ 2>/dev/null || true; }
trap cleanup SIGTERM SIGINT EXIT

tail -n0 -F "$BUS" 2>/dev/null \
  | jq --unbuffered -rc --arg startup "$STARTUP" '
      select(.tier == "alert")
      | select(.ts > $startup)
      | .summary' \
  | while IFS= read -r line; do
      apprise --tag "$TAG" --body "$line" >/dev/null 2>&1 || true
    done
