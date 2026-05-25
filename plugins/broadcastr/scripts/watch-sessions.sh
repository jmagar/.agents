#!/usr/bin/env bash
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
        --category session-doc --tier info --source inotify \
        --summary "session doc: $base" \
        --data "{\"path\":\"$path\"}"
      ;;
  esac
}

if [ "${1:-}" ]; then
  handle "$1"
  exit 0
fi

exec "$PLUGIN_ROOT/scripts/supervisor.sh" "broadcastr-sessions" \
  "$PLUGIN_ROOT/scripts/watch-sessions.sh" \
  "$REPO/docs/sessions"
