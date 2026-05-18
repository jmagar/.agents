# winbox (the `agent-os` VM)

Drive Claude's dedicated sandboxed Windows 11 VM — officially the **`agent-os`** VM (container name `agent-os-win11`, image `dockur/windows`) on host `dookie`, historically nicknamed "winbox" — through the **Windows-MCP** server installed inside it. The skill keeps the `winbox` name; both `winbox` and `agent-os` work as trigger phrases.

## What changed

This skill used to drive the VM over noVNC at `http://dookie:8006` via `agent-browser`, dispatching `MouseEvent`s on the canvas and typing one keystroke at a time. That path worked but was slow and had a known `Shift+<digit>` bug.

Windows-MCP ([CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP)) replaces it. The MCP server runs inside the agent-os VM and exposes native Windows automation as `mcp__windows-mcp__*` tools. You get a real keyboard, a real accessibility tree (`Snapshot`), and direct PowerShell (`Shell`).

## What it does

- **Look at the desktop** — `Screenshot` (fast PNG + window list) or `Snapshot` (accessibility tree with interactive element ids)
- **Interact** — `Click`, `Move`, `Scroll`, `Type`, `Shortcut`, `MultiSelect`, `MultiEdit`
- **Launch and manage** — `App` to open from Start menu, `Process` to list/kill, `Notification` to toast
- **Headless ops** — `Shell` (PowerShell), `FileSystem` (read/write/list), `Clipboard` (read/set), `Registry` (read/write/delete/list)
- **Utility** — `Wait`, `Scrape` (page text when a browser is foregrounded)

## When to invoke

Sandbox-specific triggers only: `agent-os`, `the agent-os VM`, `winbox`, `the windows sandbox`, `the dookie windows`, `drive the windows VM`, `spin up agent-os`, `open the noVNC`, or any "run X / screenshot agent-os" prompt. Does **not** fire on the user's personal Windows machine (steamy-wsl) — that target uses the `nircmd` skill.

## Connection

Configured as an HTTP MCP server in `~/.claude.json` under `mcpServers.windows-mcp` (Tailscale address + Bearer token). Claude Code reaches it automatically. Nothing to start.

If unreachable: `ssh dookie "docker ps --format '{{.Names}}' | grep agent-os"` to confirm the container (`agent-os-win11`) is up.

Side-channels exposed by the container, in case Windows-MCP is wedged:
- noVNC at `http://dookie:8006` (visual debug)
- RDP at `dookie:33890` (needs an agent-side RDP client)
- SSH at `dookie:2222` → guest port 22 (sshd inside the guest must be running; if it is, this is the cleanest scripted bypass)

## Key advantages over the legacy noVNC path

- **`Type` handles full strings reliably** — no more per-char `press` loops, no Shift-key flakiness
- **`Snapshot` returns interactive element ids** — target controls by accessibility, not pixel guessing
- **`Shell` runs PowerShell directly** — anything expressible as a command bypasses the GUI entirely
- **No browser session to manage** — no `agent-browser open`, no canvas focus juggling

## Visual debugging fallback

noVNC at `http://dookie:8006/vnc.html?autoconnect=1&resize=remote` still works for eyeballing the desktop visually, but isn't the primary interaction surface anymore. See git history of `SKILL.md` for the legacy `agent-browser` helpers if you ever need them.

## Files

- `SKILL.md` — full tool surface + recipes (open an app, run PowerShell, click by element, install via winget, paste a long string, toast a notification, persist a registry setting)
- `CHANGELOG.md` — version history

## Related skills

- `nircmd` — drives the user's *personal* Windows machine on `steamy-wsl` via NirCmd + NirSoft over SSH
- `screenshots` — Mode 2 captures the user's own desktop (not the winbox)
- `homelab-map` — full inventory of `dookie` and the other homelab hosts
