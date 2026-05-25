#!/usr/bin/env bash
# Dispatches to the compiled broadcastr-emit binary when present;
# falls back to the pure-bash emitter when the binary hasn't been built yet.
set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

if [ -x "$PLUGIN_ROOT/bin/broadcastr-emit" ]; then
  exec "$PLUGIN_ROOT/bin/broadcastr-emit" "$@"
fi

exec "$PLUGIN_ROOT/scripts/emit-fallback.sh" "$@"
