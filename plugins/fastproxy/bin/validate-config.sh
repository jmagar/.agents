#!/usr/bin/env bash
# FileChanged hook: validate proxy.json syntax when the file changes.
# Exits 0 (allow). Prints a warning to stderr on invalid JSON.
#
# Input: JSON on stdin with { "filename": "proxy.json", "path": "/abs/path/proxy.json" }

set -euo pipefail

file_path=$(jq -r '.path // ""' 2>/dev/null || echo "")

if [[ ! -f "$file_path" ]]; then
    exit 0
fi

if ! python3 -m json.tool "$file_path" > /dev/null 2>&1; then
    echo "WARNING: $file_path has invalid JSON syntax" >&2
    exit 0  # warn but don't block
fi

echo "proxy.json syntax OK"
exit 0
