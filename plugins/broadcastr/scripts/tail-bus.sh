#!/usr/bin/env bash
# Tails the per-repo and (optionally) global bus, applies self-suppression
# by $CLAUDE_SESSION_ID, drops events older than monitor startup, drops
# muted categories, and formats one display line per event to stdout.
set -uo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
REPO="${CLAUDE_PROJECT_DIR:-$PWD}"
SESSION_ID="${CLAUDE_SESSION_ID:-}"

PER_REPO_BUS="$REPO/.broadcastr/events.jsonl"
GLOBAL_HOME="${BROADCASTR_HOME:-$HOME/.claude/broadcastr}"
GLOBAL_BUS="$GLOBAL_HOME/events.jsonl"
WANT_GLOBAL="${BROADCASTR_GLOBAL_FEED:-1}"

. "$PLUGIN_ROOT/scripts/lib-jq-guard.sh"
require_jq broadcastr-feed

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
    def tier_icon:
      if .tier == "alert" then "🚨" else "📡" end;

    # Category → glyph. Group related categories to reduce visual noise.
    def category_glyph:
      if   .category == "agent-presence"                                    then "👤"
      elif (.category | test("^(commit|push|pre-commit|branch|stash)$"))   then "🌿"
      elif (.category | test("^(session-doc|plan|plan-exec)$"))            then "📝"
      elif .category == "bead"                                              then "🎯"
      else "•" end;

    # Prefer data.agent (set by session hooks) over emitter.agent mapping.
    def agent_name:
      .data.agent //
      (if .emitter.agent == "claude-code" then "Claude" else "Claude" end);

    # Human-readable summary that always leads with the agent name.
    def display_summary:
      agent_name as $ag |
      if .category == "agent-presence" then
        $ag + (if (.data.action // "joined") == "left" then " left" else " joined" end)

      elif .category == "session-doc" then
        (if .data.path then (.data.path | split("/") | last)
         else (.summary | ltrimstr("session doc: ")) end) as $fname |
        $ag + " saved: " + $fname

      elif (.category == "plan" or .category == "plan-exec") then
        (if .data.path then (.data.path | split("/") | last)
         else (.summary | ltrimstr("plan edit: ") | ltrimstr("plan-exec: ")) end) as $fname |
        $ag + " edited: " + $fname

      elif .category == "commit" then
        if (.data.subtype // "") == "merge" then
          $ag + " merged · " + (.branch // "?")
        else
          $ag + " made commit " + (.summary | ltrimstr("commit "))
        end

      elif .category == "push" then
        if (.data.subtype // "") == "attempt" then
          $ag + " pushing · " + (.branch // "?")
        elif (.tier == "alert") or (.summary | test("FAIL"; "i")) then
          $ag + "'s push FAILED · " + (.branch // "?")
        else
          $ag + " pushed · " + (.branch // "?")
        end

      elif .category == "pre-commit" then
        if (.tier == "alert") or (.summary | test("FAIL"; "i")) then
          $ag + " pre-commit FAILED · " + (.branch // "?")
        elif (.summary | test("pass"; "i")) then
          $ag + " pre-commit ✓ · " + (.branch // "?")
        else
          $ag + " pre-commit starting · " + (.branch // "?")
        end

      elif .category == "branch" then
        $ag + " switched to · " + (.data.branch // (.summary | ltrimstr("checkout: ")))

      elif .category == "bead" then
        ((.data.cmd // .summary) | ltrimstr("bd: bd ") | ltrimstr("bd ") | split(" ")) as $parts |
        ($parts[0] // "?" |
          if   . == "close"  then "closed"
          elif . == "create" then "created"
          elif . == "update" then "updated"
          elif . == "reopen" then "reopened"
          else . end) as $verb |
        ($parts | map(select(test("^beads-"))) | .[0] // "") as $issue |
        $ag + " " + $verb + (if $issue != "" then " " + $issue else "" end)

      elif .category == "stash" then
        $ag + " stashed · " + (.branch // "?")

      else .summary
      end;

    . as $e
    | select($sid == "" or .emitter.session_id == null or .emitter.session_id != $sid)
    | select(.ts > $startup)
    | select(.category as $c | $mute | index($c) | not)
    | ((.repo // "") | split("/") | last) as $proj
    | tier_icon + " " + category_glyph + "[" + $proj + "] " + display_summary
  '
}

# Dedup by event id: every emit writes to BOTH per-repo and global buses
# when BROADCASTR_GLOBAL_FEED=1, so `tail -F file1 file2` sees the same
# event twice. Strip duplicates by ULID before formatting. The seen-set
# is bulk-purged every 10k entries to keep memory bounded for long
# sessions; the dup window in practice is sub-second so a periodic flush
# loses nothing real.
dedup_events() {
  awk '
    {
      if (match($0, /"id":"evt_[^"]+"/)) {
        id = substr($0, RSTART, RLENGTH)
        if (!(id in seen)) {
          seen[id] = 1
          print; fflush()
        }
        if (length(seen) > 10000) delete seen
      } else {
        print; fflush()
      }
    }
  '
}

cleanup() { pkill -P $$ 2>/dev/null || true; }
trap cleanup SIGTERM SIGINT EXIT

if [ "$WANT_GLOBAL" != "0" ]; then
  tail -n0 -F "$PER_REPO_BUS" "$GLOBAL_BUS" 2>/dev/null \
    | grep --line-buffered -v "^==>" \
    | dedup_events \
    | format_line &
else
  tail -n0 -F "$PER_REPO_BUS" 2>/dev/null | format_line &
fi
wait
