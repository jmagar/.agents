#!/usr/bin/env bash
# Block until the fastproxy /health endpoint returns status "ok".
# Used in CI pipelines and docker-compose health checks.
#
# Usage:
#   ./bin/wait-for-proxy.sh [base-url] [timeout-seconds]
#   ./bin/wait-for-proxy.sh http://localhost:8000 30

set -euo pipefail

BASE_URL="${1:-${FASTPROXY_BASE_URL:-http://localhost:8000}}"
TIMEOUT="${2:-30}"
ENDPOINT="${BASE_URL}/health"

echo "Waiting for proxy at $ENDPOINT (timeout: ${TIMEOUT}s)..."

start=$(date +%s)
while true; do
    if response=$(curl -sf --max-time 2 "$ENDPOINT" 2>/dev/null); then
        s=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
        if [[ "$s" == "ok" ]]; then
            echo "Proxy is healthy."
            exit 0
        fi
    fi

    now=$(date +%s)
    elapsed=$(( now - start ))
    if (( elapsed >= TIMEOUT )); then
        echo "ERROR: proxy not healthy after ${TIMEOUT}s" >&2
        exit 1
    fi

    sleep 1
done
