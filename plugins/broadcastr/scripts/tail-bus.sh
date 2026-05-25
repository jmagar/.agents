#!/usr/bin/env bash
# Tails the per-repo and (optionally) global bus, applies self-suppression
# by $CLAUDE_SESSION_ID, drops events older than monitor startup, drops
# muted categories, and formats one display line per event to stdout.
set -uo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
REPO="${CLAUDE_PROJECT_DIR:?must set CLAUDE_PROJECT_DIR}"
SESSION_ID="${CLAUDE_SESSION_ID:-}"

PER_REPO_BUS="$REPO/.broadcastr/events.jsonl"
GLOBAL_HOME="${BROADCASTR_HOME:-$HOME/.claude/broadcastr}"
GLOBAL_BUS="$GLOBAL_HOME/events.jsonl"
WANT_GLOBAL="${BROADCASTR_GLOBAL_FEED:-1}"

# Fail loudly at startup if jq is missing — otherwise the filter pipeline
# would silently produce zero output and the user would see no feed.
if ! command -v jq >/dev/null 2>&1; then
  echo "broadcastr-feed: jq not installed; feed monitor exiting" >&2
  "$PLUGIN_ROOT/scripts/emit.sh" \
    --category agent-presence --tier alert --source claude-hook \
    --summary "broadcastr-feed: jq missing; feed disabled this session" \
    --data '{"monitor":"broadcastr-feed"}' 2>/dev/null || true
  exit 0
fi

mkdir -p "$(dirname "$PER_REPO_BUS")"
touch "$PER_REPO_BUS"
if [ "$WANT_GLOBAL" != "0" ]; then
  mkdir -p "$GLOBAL_HOME"
  touch "$GLOBAL_BUS"
fi

MUTE_LIST="${BROADCASTR_MUTE:-}"
MUTE_JQ='[]'
if [ -n "$MUTE_LIST" ]; then
  MUTE_JQ="$(printf '%s' "$MUTE_LIST" | tr ',' '\n' | jq -R . | jq -s .)"
fi

STARTUP="$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"

format_line() {
  jq --unbuffered -rc --arg sid "$SESSION_ID" --arg startup "$STARTUP" --argjson mute "$MUTE_JQ" '
    . as $e
    | select((.emitter.session_id // "") != $sid)
    | select(.ts > $startup)
    | select(.category as $c | $mute | index($c) | not)
    | "[" + .tier + "] " + .category + " · " + .summary + " · " + (.emitter.agent // "?") + "@" + (.emitter.host // "?")
  '
}

cleanup() { pkill -P $$ 2>/dev/null || true; }
trap cleanup SIGTERM SIGINT EXIT

if [ "$WANT_GLOBAL" != "0" ]; then
  tail -n0 -F "$PER_REPO_BUS" "$GLOBAL_BUS" 2>/dev/null | grep --line-buffered -v "^==>" | format_line &
else
  tail -n0 -F "$PER_REPO_BUS" 2>/dev/null | format_line &
fi
wait
