#!/usr/bin/env bash
# Check the fastproxy /health endpoint and print a compact status summary.
# Exits 0 if status is "ok", 1 if "degraded" or "error", 2 if unreachable.
#
# Usage:
#   ./bin/health-check.sh [base-url]
#   ./bin/health-check.sh http://localhost:8000

set -euo pipefail

BASE_URL="${1:-${FASTPROXY_BASE_URL:-http://localhost:8000}}"
ENDPOINT="${BASE_URL}/health"

if ! response=$(curl -sf --max-time 5 "$ENDPOINT" 2>/dev/null); then
    echo "ERROR: proxy unreachable at $ENDPOINT" >&2
    exit 2
fi

status=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))")
storage=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('storage','unknown'))")
sessions=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('active_sessions',0))")

echo "status:   $status"
echo "storage:  $storage"
echo "sessions: $sessions"
echo ""
echo "$response" | python3 -c "
import sys, json
d = json.load(sys.stdin)
servers = d.get('servers', {})
if servers:
    print('servers:')
    for alias, s in servers.items():
        print(f'  {alias}: {s}')
"

case "$status" in
    ok) exit 0 ;;
    *) exit 1 ;;
esac
