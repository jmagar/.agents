---
description: Block a tool for a specific user via the admin API
argument-hint: <user-id> <server__tool_name>
allowed-tools: Bash(bash:*)
---

Block a namespaced tool for a specific user. The change applies live to all
active sessions for that user — no reconnect required.

Parse `$ARGUMENTS` as: `<user-id> <server__tool_name>`

If either is missing, ask for it before proceeding.

## Validation

1. Confirm the tool name follows `server_alias__tool_name` format:
   - The separator is exactly two underscores (`__`)
   - Server alias: lowercase letters, digits, underscores (hyphens already converted)
   - Tool name: lowercase letters, digits, underscores, hyphens — pattern `[a-z0-9_-]+__[a-z0-9_-]+`
   - If the name has hyphens in the alias part, warn the user — hyphens become underscores in
     the proxy namespace (e.g. `my-server__read_file` → `my_server__read_file`)

2. Run `./bin/health-check.sh` — if the proxy is unhealthy, warn and ask whether to proceed.

## Apply

Spawn `fastproxy-admin` to apply the blocklist change for the given user and tool.

After the change is applied, ask `fastproxy-admin` to list the user's current blocklist
to confirm the tool appears in it.

Note: FastMCP sends `tools/list_changed` automatically — do NOT send it manually.
