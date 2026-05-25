#!/usr/bin/env bash
# Optional: shell wrapper that observes `git push` outcome.
# Source this from your shell rc, then `alias git-push=broadcastr-push`.
set -uo pipefail
PLUGIN_ROOT="${BROADCASTR_PLUGIN_ROOT:-$HOME/.claude/plugins/broadcastr}"

broadcastr-push() {
  local out
  local rc=0
  local branch
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"

  if out=$(git push "$@" 2>&1); then
    "$PLUGIN_ROOT/scripts/emit.sh" \
      --category push --tier info --source cli \
      --branch "$branch" \
      --summary "push succeeded: $branch" \
      --data "{\"subtype\":\"success\"}"
    printf '%s\n' "$out"
  else
    rc=$?
    "$PLUGIN_ROOT/scripts/emit.sh" \
      --category push --tier alert --source cli \
      --branch "$branch" \
      --summary "push FAILED: $branch (exit $rc)" \
      --data "{\"subtype\":\"fail\",\"exit\":$rc}"
    printf '%s\n' "$out" >&2
    return $rc
  fi
}
