#!/usr/bin/env bash
# inotify producer for plan dirs. Invoked two ways:
#   * No args: bootstrap mode — exec the supervisor pointing back at this script.
#   * One arg "<path>|<event>": handler mode — process a single inotify event.
set -euo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
REPO="${CLAUDE_PROJECT_DIR:?must set CLAUDE_PROJECT_DIR}"

handle() {
  local line="$1"
  local path="${line%|*}"
  case "$path" in
    *.md)
      local base
      base="$(basename "$path")"
      "$PLUGIN_ROOT/scripts/emit.sh" \
        --category plan --tier info --source inotify \
        --summary "plan edit: $base" \
        --data "{\"path\":\"$path\"}"
      # plan-exec marker: detect when a step is being checked off
      if grep -qE '^- \[(x|X)\] \*\*Step' "$path" 2>/dev/null; then
        "$PLUGIN_ROOT/scripts/emit.sh" \
          --category plan-exec --tier info --source inotify \
          --summary "plan progress: $base" \
          --data "{\"path\":\"$path\"}"
      fi
      ;;
  esac
}

if [ "${1:-}" ]; then
  handle "$1"
  exit 0
fi

exec "$PLUGIN_ROOT/scripts/supervisor.sh" "broadcastr-plans" \
  "$PLUGIN_ROOT/scripts/watch-plans.sh" \
  "$REPO/docs/plans" "$REPO/docs/superpowers/plans"
