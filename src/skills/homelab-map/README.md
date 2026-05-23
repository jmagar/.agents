# homelab-map

Authoritative map of Jacob's WillyNet homelab. Triggers strictly on named devices.

## What it does
Tells the agent which host runs which service before it touches anything. Covers six devices — tootie, dookie, shart, squirts, steamy/steamy-wsl, vivobook/vivobook-wsl — plus network topology, MCP servers, storage layout, backup chains, known issues.

## When to invoke
Any prompt naming one of the devices, or `WillyNet`. Strict device-name fidelity — won't fire on generic "my homelab" / "my server" / "my NAS" prompts.

## Files
- `SKILL.md` — lean overview: nodes-at-a-glance table, service→host lookup, conventions
- `references/homelab.md` — generated runtime inventory, read on demand
- `scripts/generate-homelab-report.py` — pulls host/container/storage/proxy state and rewrites `references/homelab.md`

## Updating
Regenerate the report instead of hand-maintaining runtime values:

```bash
python3 src/skills/homelab-map/scripts/generate-homelab-report.py
```

The generator uses non-interactive SSH plus Docker/ZFS/Unraid/SWAG shell probes. Container counts, RAM%, uptime etc. are point-in-time; rerun before acting on anything current-state dependent.
