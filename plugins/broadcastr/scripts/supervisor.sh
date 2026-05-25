#!/usr/bin/env bash
# Generic supervisor for inotify watchers. Restarts the watcher on transient
# failure. On a clear "can't arm" error (watch limit, missing dir we can't
# create), emits one alert and exits so silence is visible.
set -uo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
NAME="$1"; shift
# The first positional arg after NAME is the per-event handler command;
# remaining args are the directories to watch.
HANDLER="$1"; shift
TARGETS=("$@")

if ! command -v inotifywait >/dev/null 2>&1; then
  "$PLUGIN_ROOT/scripts/emit.sh" \
    --category agent-presence --tier alert --source claude-hook \
    --summary "broadcastr: inotifywait not installed; ${NAME} disabled" \
    --data "{\"monitor\":\"$NAME\"}"
  exit 0
fi

# Pre-create any target directories so inotifywait doesn't bail on missing paths
for d in "${TARGETS[@]}"; do
  mkdir -p "$d" 2>/dev/null || true
done

# Test-arm once; if even the first arm fails (rc != 2/timeout), treat as structural.
inotifywait -q -t 1 -e create "${TARGETS[@]}" >/dev/null 2>&1
rc=$?
# 0 = event seen during the 1s window, 2 = timeout (arm worked but no event)
if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
  "$PLUGIN_ROOT/scripts/emit.sh" \
    --category agent-presence --tier alert --source claude-hook \
    --summary "broadcastr: ${NAME} failed to arm, FS events disabled" \
    --data "{\"monitor\":\"$NAME\",\"exit\":$rc}"
  exit 0
fi

trap 'kill 0 2>/dev/null; exit 0' SIGTERM SIGINT

while true; do
  while IFS= read -r line; do
    "$HANDLER" "$line" || true
  done < <(inotifywait -m -q -e close_write,create,moved_to --format '%w%f|%e' "${TARGETS[@]}" 2>/dev/null)
  sleep 1
done
