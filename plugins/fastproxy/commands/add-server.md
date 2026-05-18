---
description: Add a new upstream MCP server to the proxy config
argument-hint: <alias> [transport] [command-or-url]
allowed-tools: Read, Write, Bash(bash:*)
---

Register a new upstream MCP server in `proxy.json`.

Parse `$ARGUMENTS` as: `<alias> [transport] [command-or-url]`

Ask for any missing required fields:
- `alias` — short name, `[a-z0-9-]+` (hyphens allowed; become underscores in tool names)
- `transport` — `stdio`, `http`, or `sse`
- `command` (stdio) or `url` (http/sse)
- `args` (optional, stdio only)
- `env` (optional — use `${VAR}` for interpolated values)
- `tags` (optional — add `"cacheable"` only for tools that return identical results for identical
  inputs regardless of which user calls them; never use for user-specific data)

## Steps

1. Read `proxy.json` — if it does not exist, stop and tell the user to create one first.

2. Validate the alias:
   - Must match `[a-z0-9-]+`
   - If the alias is already present in `servers`, ask: update the existing entry or abort?
     Do not overwrite silently.

3. Add the server entry under `servers`.

4. Write updated `proxy.json`.

5. The config watcher picks up the change automatically — no restart needed.

6. Run `./bin/health-check.sh` and confirm the new server alias appears with status `ok`.
   If it shows `down`, report the health response and suggest checking the command/URL.
