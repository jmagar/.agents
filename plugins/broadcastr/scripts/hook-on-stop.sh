#!/usr/bin/env bash
set -euo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
"$PLUGIN_ROOT/scripts/emit.sh" \
  --category agent-presence --tier info --source claude-hook \
  --summary "claude session left" \
  --data '{"action":"left"}'
