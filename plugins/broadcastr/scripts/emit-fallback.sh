#!/usr/bin/env bash
# Pure-bash emit fallback used until bin/broadcastr-emit is compiled.
# Trades latency for portability. Generates a Crockford-base32-ish
# 26-char random suffix; not RFC-compliant ULID monotonicity, but
# collision-resistant within a session.
set -euo pipefail

[ "${BROADCASTR_DISABLED:-}" = "1" ] && exit 0

CATEGORY="" TIER="" SUMMARY="" SOURCE=cli DATA="{}" BRANCH=""
while [ $# -gt 0 ]; do
  case "$1" in
    --category) CATEGORY="$2"; shift 2;;
    --tier) TIER="$2"; shift 2;;
    --summary) SUMMARY="$2"; shift 2;;
    --source) SOURCE="$2"; shift 2;;
    --data) DATA="$2"; shift 2;;
    --branch) BRANCH="$2"; shift 2;;
    *) shift;;
  esac
done

REPO="${CLAUDE_PROJECT_DIR:-$PWD}"
PER_REPO_BUS="$REPO/.broadcastr/events.jsonl"
GLOBAL_HOME="${BROADCASTR_HOME:-$HOME/.claude/broadcastr}"
GLOBAL_BUS="$GLOBAL_HOME/events.jsonl"

TS="$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
# 26-char Crockford-base32 random suffix from 16 bytes of urandom
RAND="$(head -c 16 /dev/urandom | LC_ALL=C tr -dc '0-9A-HJKMNP-TV-Z' | head -c 26)"
# Pad if entropy was thin (extremely rare)
while [ "${#RAND}" -lt 26 ]; do
  RAND="${RAND}$(head -c 4 /dev/urandom | LC_ALL=C tr -dc '0-9A-HJKMNP-TV-Z')"
done
ID="evt_${RAND:0:26}"

SESSION_ID="${CLAUDE_SESSION_ID:-}"
AGENT="user"
[ -n "$SESSION_ID" ] && AGENT="claude-code"

HOST="${HOSTNAME:-$(hostname)}"
USER_NAME="${USER:-$(id -un)}"

json_string() {
  # Encode a string as a JSON-quoted value using jq when available, else best-effort
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$1" | jq -Rs .
  else
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    printf '"%s"' "$s"
  fi
}

SUMMARY_JSON="$(json_string "$SUMMARY")"

SID_JSON='null'
[ -n "$SESSION_ID" ] && SID_JSON="$(json_string "$SESSION_ID")"

BRANCH_FIELD=""
[ -n "$BRANCH" ] && BRANCH_FIELD=",\"branch\":$(json_string "$BRANCH")"

LINE=$(printf '{"ts":"%s","id":"%s","tier":"%s","category":"%s","source":"%s","emitter":{"session_id":%s,"agent":"%s","host":"%s","user":"%s"},"repo":"%s"%s,"summary":%s,"data":%s}' \
  "$TS" "$ID" "$TIER" "$CATEGORY" "$SOURCE" "$SID_JSON" "$AGENT" "$HOST" "$USER_NAME" "$REPO" "$BRANCH_FIELD" "$SUMMARY_JSON" "$DATA")

append_with_rotate() {
  local bus="$1"
  mkdir -p "$(dirname "$bus")"
  local max="${BROADCASTR_BUS_MAX_BYTES:-5242880}"
  local retain="${BROADCASTR_BUS_RETAIN:-3}"

  if [ -f "$bus" ]; then
    local size
    size=$(stat -c %s "$bus" 2>/dev/null || stat -f %z "$bus" 2>/dev/null || echo 0)
    if [ "$size" -ge "$max" ]; then
      local lock="${bus}.rotate.lock"
      (
        if flock -n 9; then
          # re-check under lock
          local s2
          s2=$(stat -c %s "$bus" 2>/dev/null || stat -f %z "$bus" 2>/dev/null || echo 0)
          if [ "$s2" -ge "$max" ]; then
            local i=$((retain - 1))
            while [ "$i" -ge 1 ]; do
              [ -f "${bus}.${i}" ] && mv "${bus}.${i}" "${bus}.$((i+1))"
              i=$((i-1))
            done
            mv "$bus" "${bus}.1"
            : > "$bus"
          fi
        fi
      ) 9>"$lock"
    fi
  fi
  printf '%s\n' "$LINE" >> "$bus"
}

append_with_rotate "$PER_REPO_BUS"

if [ "${BROADCASTR_GLOBAL_FEED:-1}" != "0" ]; then
  append_with_rotate "$GLOBAL_BUS"
fi
