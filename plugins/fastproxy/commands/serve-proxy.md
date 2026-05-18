---
description: Start the fastproxy OAuth MCP gateway
argument-hint: [--host HOST] [--port PORT] [--config PATH]
allowed-tools: Read, Bash(fastproxy:*), Bash(bash:*)
---

Start the fastproxy HTTP server. Parse `$ARGUMENTS` for optional flags:

- `--host` (default: `0.0.0.0`)
- `--port` (default: `8000`)
- `--config` (default: `proxy.json`)

## Pre-flight

1. Check `FASTPROXY_JWT_SECRET` is set — if missing, stop and tell the user:
   > Set `FASTPROXY_JWT_SECRET` before starting: `export FASTPROXY_JWT_SECRET=<secret>`

2. Verify the config file exists (`proxy.json` or the value from `--config`).
   If missing, stop and tell the user to create or specify one.

3. Verify the config file is valid JSON — if not, report the parse error and stop.

4. Verify the `fastproxy` binary is on PATH — if not, tell the user to install:
   > `pip install fastproxy` or `uv tool install fastproxy`

## Start

Run: `fastproxy serve $ARGUMENTS`

Wait for the server to emit its startup log line, then run `./bin/health-check.sh`
to confirm the proxy is accepting requests.

If the health check fails, report the raw output and suggest:
- Port already in use → try `--port 8001` (or identify the blocking process)
- Storage backend error → check Redis connectivity with `docker compose ps redis`
