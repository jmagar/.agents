---
name: homelab-map
description: 'This skill should be used whenever a prompt mentions any of Jacob''s named homelab hosts — **tootie, dookie, shart, squirts, steamy, steamy-wsl, vivobook, vivobook-wsl** — or the **WillyNet** LAN. It provides the authoritative map of which host runs which service, IPs, ports, SSH details, storage layout, backup chains, MCP server locations, and known issues. Example triggers: "what''s on dookie", "is plex running on tootie", "ssh into squirts", "where''s the qdrant container", "which box has the GPU", "check shart''s backup status", "the steamy box", "ssh steamy-wsl", "vivobook-wsl logs". Does NOT fire on generic "my homelab" / "my server" / "my NAS" prompts that don''t name a specific host. Full inventory in `references/homelab.md` — read that file whenever detail beyond the SKILL.md overview is needed.'
---

# homelab-map

Quick map of Jacob's homelab. **Full inventory in `references/homelab.md` — read that file the moment you need anything more specific than this overview.**

## Nodes at a glance

| Name | Role | LAN IP | OS | Notes |
|---|---|---|---|---|
| **tootie** | Primary NAS / app server | 10.1.0.2 | Unraid 7.2.4 (i7-13700K, 128GB) | ~65 containers. Web: `:6969`. SSH port `29229`. Also runs dookie as a KVM guest. **⚠ no parity disk currently.** |
| **dookie** | Dev / AI / MCP hub | 10.1.0.6 | Debian (KVM guest on tootie, also direct LAN) | Axon RAG stack, synapse-mcp (3000), syslog-mcp (1514/3100), arcane-mcp (44332), unraid-mcp (6970). The Windows 11 sandbox container (dockur/windows) at `:8006` also lives here. |
| **squirts** | Edge services | 10.1.0.8 | Ubuntu (4 cores, 15GB) | SWAG (128 vhosts), Authelia, AdGuard, Gotify, MCP gateway, Vaultwarden, Paperless, etc. **RAM 84% — tight.** |
| **shart** | ZFS backup target | 169.254.80.235 (link-local — verify) | Unraid | ZFS `backup` pool 7.27TB / 23% used. Receives nightly Syncoid streams from tootie + squirts. |
| **steamy** | GPU workloads (RTX 4070) | 10.1.0.65 | Win11 + WSL2 | `crawl4r-qdrant` (GPU qdrant). Hosts the user's actual desktop — `ssh steamy-wsl` is the default target for the `screenshots`, `clipboard`, `nircmd` skills. |
| **vivobook** | Mobile dev laptop | 10.1.0.5 (when docked) | Win11 + WSL2 | Just an `arcane-agent`. |

All nodes joined to **Tailscale** mesh (`100.x.y.z`). Router is a UniFi UCG-Max ("The Mothership"). WiFi SSID `WillyNet`. Public services live at `*.tootie.tv` via SWAG.

## "Where does X live" — quick lookups

| If the user mentions… | It's on… |
|---|---|
| Plex, Sonarr, Radarr, Bazarr, Prowlarr, qBittorrent, Sabnzbd, Tautulli, Immich, Audiobookshelf, Kavita, Navidrome | tootie |
| Axon, Qdrant (CPU), TEI/Qwen3-Embedding, Ollama, mem0, axon-postgres/redis/chrome, pulse_neo4j | dookie |
| GPU qdrant (`crawl4r-qdrant`), anything with `gpu-nvidia` | steamy |
| SWAG, Authelia, AdGuard, Gotify, Vaultwarden, Paperless, FreshRSS, Linkding, Karakeep, Memos, Radicale, Searxng, Dockge, Dozzle, multi-scrobbler/maloja, RustDesk | squirts |
| Sanoid / Syncoid backups, ZFS receive | shart |
| Portainer, Watchtower, Glances, Scrutiny, Vnstat, code-server, Firefox, Joplin, Bytestash, Open WebUI, Affine, Homebox, Homarr, Notifiarr, Infisical, Apprise, sshwifty, change-detection, Esphome, Syncthing | tootie |
| **MCP servers** — synapse, syslog, arcane, unraid, swag, unifi, gotify, overseerr, plex, radarr, sonarr, prowlarr, sabnzbd, tautulli, qbittorrent, portainer, mcphub, mcp-context-forge | mostly **tootie + dookie + squirts** — see references/homelab.md §"MCP Server Ecosystem" for exact host |
| Windows sandbox (dookie:8006 noVNC), winbox skill target | dookie (dockur/windows container) |

## Conventions

- **All scatological naming.** Don't be cute about it — they are named tootie, dookie, shart, squirts. Use the names verbatim.
- **`steamy-wsl` ≠ `steamy`** in skill defaults: most skills (`screenshots`, `clipboard`, `nircmd`, `chrome`) target the WSL2 alias because the actual user desktop / win11 box is reached via WSL ssh.
- **`*.tootie.tv` = SWAG vhost on squirts**, fronts a service running anywhere. Don't assume the service is on tootie just because of the domain.
- **arcane-agent runs on every node** — it manages local compose projects. Different versions across nodes (drift documented in references).
- **Public SSH does not exist.** All inter-node SSH goes through the Tailscale mesh.

## When to read the reference doc

Read `references/homelab.md` whenever you need:
- Exact container lists per host
- Storage layout (Unraid disk slots, ZFS pools, share-level breakdowns)
- Backup chains (which datasets replicate where)
- All 128 SWAG vhosts
- Vulnerability scan numbers
- Known issues / tech debt log
- Specific port numbers beyond the headline ones above

`grep` the reference file — it's structured with clear headers (`## Nodes`, `## Storage Architecture`, `## Service Catalog`, `## AI / RAG / Agent Stack`, `## MCP Server Ecosystem`, `## Known Issues & Tech Debt`, etc.)

## Updating this skill

This map was seeded from a live MCP sweep on 2026-03-31. Treat container counts, RAM%, uptime numbers etc. as **point-in-time** — re-verify via `arcane-mcp` / `syslog` / `ssh <host> docker ps` before acting on anything that depends on current state. Names of nodes, IPs, roles, and architectural choices are stable.

If you notice the reference is stale in a load-bearing way (a service moved hosts, a node was added/renamed, a critical port changed), update `references/homelab.md` *and* this overview before the session ends.
