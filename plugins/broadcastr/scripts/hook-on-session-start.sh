#!/usr/bin/env bash
set -euo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

CWD="${CLAUDE_PROJECT_DIR:-}"
SUMMARY="claude session joined: ${CWD:-?}"

# Build --data via jq so a CWD with quotes/backslashes/newlines doesn't
# corrupt the event JSON.
DATA="$(jq -nc --arg cwd "$CWD" '{action:"joined", cwd:$cwd}' 2>/dev/null || echo '{"action":"joined"}')"

"$PLUGIN_ROOT/scripts/emit.sh" \
  --category agent-presence --tier info --source claude-hook \
  --summary "$SUMMARY" \
  --data "$DATA"
