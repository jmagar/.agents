#!/usr/bin/env bash
set -euo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
agent_label() {
  local agent="${BROADCASTR_AGENT_NAME:-${BROADCASTR_AGENT:-}}"
  case "${agent,,}" in
    codex) printf 'Codex' ;;
    gemini) printf 'Gemini' ;;
    claude|claude-code|"") printf 'Claude' ;;
    *) printf '%s' "$agent" ;;
  esac
}

AGENT="$(agent_label)"
"$PLUGIN_ROOT/scripts/emit.sh" \
  --category agent-presence --tier info --source claude-hook \
  --summary "${AGENT} left" \
  --data "$(jq -nc --arg agent "$AGENT" '{action:"left", agent:$agent}' 2>/dev/null || echo '{"action":"left"}')"
