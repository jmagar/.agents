#!/usr/bin/env bash
set -euo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SUMMARY="claude session joined: ${CLAUDE_PROJECT_DIR:-?}"
"$PLUGIN_ROOT/scripts/emit.sh" \
  --category agent-presence --tier info --source claude-hook \
  --summary "$SUMMARY" \
  --data "{\"action\":\"joined\",\"cwd\":\"${CLAUDE_PROJECT_DIR:-}\"}"
