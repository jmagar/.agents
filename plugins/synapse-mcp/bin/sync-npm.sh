#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
DATA_ROOT="${CLAUDE_PLUGIN_DATA:-${REPO_ROOT}}"

SRC_LOCK="${REPO_ROOT}/package-lock.json"
DST_LOCK="${DATA_ROOT}/package-lock.json"

if [[ ! -f "${SRC_LOCK}" ]]; then
  echo "sync-npm.sh: missing lockfile at ${SRC_LOCK}" >&2
  exit 1
fi

if diff -q "${SRC_LOCK}" "${DST_LOCK}" >/dev/null 2>&1; then
  exit 0
fi

mkdir -p "${DATA_ROOT}"

if cp "${REPO_ROOT}/package.json" "${DATA_ROOT}/package.json" && \
   cp "${SRC_LOCK}" "${DST_LOCK}" && \
   npm ci --prefix "${DATA_ROOT}"; then
  :
else
  rm -f "${DST_LOCK}"
  exit 1
fi
