#!/usr/bin/env bash
# Generate a FASTPROXY_JWT_SECRET suitable for production use.
# Prints a 64-character hex string to stdout.
#
# Usage:
#   ./bin/gen-secret.sh
#   FASTPROXY_JWT_SECRET=$(./bin/gen-secret.sh)

set -euo pipefail

openssl rand -hex 32
