# homelab-map

Authoritative map of Jacob's WillyNet homelab. Triggers strictly on named devices.

## What it does
Tells the agent which host runs which service before it touches anything. Covers six devices — tootie, dookie, shart, squirts, steamy/steamy-wsl, vivobook/vivobook-wsl — plus network topology, MCP servers, storage layout, backup chains, known issues.

## When to invoke
Any prompt naming one of the devices, or `WillyNet`. Strict device-name fidelity — won't fire on generic "my homelab" / "my server" / "my NAS" prompts.

## Files
- `SKILL.md` — lean overview: nodes-at-a-glance table, service→host lookup, conventions
- `references/homelab.md` — full inventory (~700 lines, read on demand)

## Updating
SKILL.md and references/homelab.md were seeded from a live MCP sweep on 2026-03-31. Container counts, RAM%, uptime etc. are point-in-time — verify via `arcane-mcp` / `syslog` / `ssh <host> docker ps` before acting on anything that depends on current state. Node names, IPs, roles are stable.
