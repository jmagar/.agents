# WillyNet Homelab - Infrastructure Documentation

> Seeded from live MCP sweep: 2026-03-31
> Refreshed from Arcane, SWAG, Syslog, and SSH checks: 2026-05-22
> Owner: Jacob Magar (jmagar), Columbia, SC

---

## Table of Contents

1. [Overview](#overview)
2. [Network Topology](#network-topology)
3. [Nodes](#nodes)
4. [Storage Architecture](#storage-architecture)
5. [Backup Strategy](#backup-strategy)
6. [Reverse Proxy & Public Services](#reverse-proxy--public-services)
7. [Service Catalog](#service-catalog)
8. [AI / RAG / Agent Stack](#ai--rag--agent-stack)
9. [MCP Server Ecosystem](#mcp-server-ecosystem)
10. [Monitoring & Notifications](#monitoring--notifications)
11. [Virtual Machines](#virtual-machines)
12. [Security Posture](#security-posture)
13. [Known Issues & Tech Debt](#known-issues--tech-debt)

---

## Overview

| Metric | Value |
|---|---|
| Total nodes | 6 (4 hardware + 2 WSL VMs) |
| Total containers running | ~110 fleet-wide from SSH checks (tootie 49, dookie 19, squirts 37, shart 3, steamy-wsl 1, vivobook-wsl 1) |
| Total storage capacity | ~210 TB (unRAID array) + ~14 TB (ZFS) + ~6 TB NVMe |
| Active SWAG proxy configs | 149 |
| Gotify notification apps | 19 |
| UniFi clients | Not refreshed on 2026-05-22; UniFi client API returned an error |
| Syslog volume | 5.82M entries written in current runtime counters; host table below spans 2026-05-12 onward |

**Theme:** All nodes follow a scatological naming convention. Network is `WillyNet`. Most services are accessible via `*.tootie.tv` subdomains via SWAG.

---

## Network Topology

### Internet & Routing

- **Primary WAN:** ATT (residential fiber/cable)
- **Secondary WAN:** Internet 2 (failover/load-balance, configured in UniFi)
- **Router:** UniFi Cloud Gateway Max (UCG-Max) — "The Mothership"
- **WiFi AP:** UniFi U7 Pro (WiFi 7) — "Axilla"
- **SSID:** `WillyNet` · WPA2-PSK · 2.4/5/6 GHz
- **LAN subnet:** `10.1.0.0/24` (DHCP via UCG-Max)
- **Tailscale mesh:** All nodes joined (CGNAT range `100.x.y.z`)
- **UniFi alarms/events:** not refreshed on 2026-05-22; the UniFi clients action failed via Lab.

### Key IPs (10.1.0.0/24)

| Host | IP | Type | Notes |
|---|---|---|---|
| Cloud Gateway Max | `10.1.0.1` | router | "The Mothership" |
| tootie | `10.1.0.2` | wired | unRAID NAS |
| pixel | `10.1.0.4` | wifi | phone |
| vivobook-wsl | `10.1.0.5` | wired | WSL dev machine |
| dookie | `10.1.0.6` | wired | dev/AI box |
| squirts | `10.1.0.8` | wired | edge services |
| steamy-wsl | `10.1.0.65` | wired | GPU box (Win11 + WSL2) |
| iPhone | `10.1.0.66` | wifi | |
| Nest Thermostat | `10.1.0.90` | wifi | |
| iPad | `10.1.0.197` | wifi | |
| shart | `10.1.0.3` | wired | also has `169.254.80.235` on `shim-br0` |

### Tailscale IPs (selected)

| Host | Tailscale IP |
|---|---|
| dookie | `100.88.16.79` |
| tootie | `100.120.242.29` (ssh port 29229) |
| squirts | `100.75.111.118` |
| shart | `100.118.209.1` |
| steamy-wsl | `100.74.16.82` |
| vivobook-wsl | `100.104.50.17` |

### Wireless Clients

Not refreshed on 2026-05-22. The previous March 2026 snapshot listed 26 connected wireless clients, including Nest Audio/Home devices, Chromecast Audio, Living Room TV, Nursery Camera + Light, ESPHome smart lights, and Wyze Cam.

---

## Nodes

### tootie — Primary NAS

The center of gravity. Houses media, applications, databases, AI services, and most of the Docker fleet.

| Property | Value |
|---|---|
| Role | Primary NAS / app server |
| IP | `10.1.0.2` (LAN) / `100.120.242.29` (TS) |
| OS | Unraid OS **7.2.4** (kernel 6.12.54) |
| CPU | Intel **i7-13700K** (16 cores / 24 threads, up to 5.4 GHz) |
| RAM | 128 GB reported by Unraid/Linux (`free` shows 125 GiB usable) |
| Motherboard | MSI PRO Z790-A WIFI DDR4 |
| Web UI | http://10.1.0.2:6969 (HTTP) / :31337 (HTTPS) |
| SSH | port 29229 |
| Uptime | 3w 5d |
| Containers | 49 running |
| Live CPU | not refreshed |
| Live RAM | 94 GiB / 125 GiB used |

**Hardware unique to tootie:**
- 13× spinning disks (data array, no parity)
- 3× NVMe cache pools (ZFS)
- Unraid GraphQL API + `unraid-mcp` connector

---

### dookie — Dev / AI / MCP Hub

Where the active development, RAG pipeline, and MCP servers live.

| Property | Value |
|---|---|
| Role | Dev box, Axon/RAG infrastructure, MCP services |
| IP | `10.1.0.6` (LAN) / `100.88.16.79` (TS) |
| Hostname | `dookie` (also runs as KVM guest on tootie via libvirt) |
| OS | Debian Linux |
| CPU | 23 cores reported (likely passthrough/vCPUs from tootie host) |
| RAM | 59 GB total |
| Uptime | 2d 1h |
| Containers | 19 running |
| Live CPU | not refreshed |
| Live RAM | 50 GiB / 57 GiB used |
| Load avg | not refreshed |

**Note:** dookie is a VM running on tootie (state: `RUNNING` in libvirt). It's also reachable directly over the LAN as `10.1.0.6`.

**Notable containers on dookie:**
- `axon-qdrant` (v1.13.1) — vector store
- `axon-tei` — HuggingFace TEI `89-1.9`, serving **Qwen/Qwen3-Embedding-0.6B** (float16)
- `axon` — dev runtime on port 8001
- `axon-chrome` — headless Chrome for scraping
- `syslog-mcp` — `ghcr.io/jmagar/syslog-mcp:0.27.1`, ports 1514 (TCP/UDP) + 3100 (HTTP)
- `arcane-mcp` — port 44332
- `unraid-mcp` — `unrust:dev`, port 40010
- `gotify-mcp`, `unifi-mcp`, `tailscale-mcp`, `apprise-mcp`, `example-mcp` — ports 40020-40060
- `labby` — Lab control plane, port 8765
- `arcane-agent` (v1.19.4) — manages `/home/jmagar/compose`
- `dockersocket` proxy (Tecnativa)
- `agent-os-win11` (dockurr/windows) — Windows 11 sandbox at `:8006` (noVNC), `:33890` (RDP), `:2222` (SSH). This is the **winbox** skill target.
- `agentmemory-iii-engine-1`, `aurora-design-system`, `open-design`

---

### squirts — Services / Edge Node

Auth, networking, and lighter services.

| Property | Value |
|---|---|
| Role | Edge services, SWAG, Authelia, MCP gateways |
| IP | `10.1.0.8` |
| Hostname | `squirts` |
| OS | Ubuntu Linux |
| CPU | 4 cores (Intel NUC class) |
| RAM | 15 GB total |
| Uptime | 2d 1h |
| Containers | 37 running |
| Live CPU | not refreshed |
| Live RAM | 10 GiB / 14 GiB used |
| ZFS | `bpool` 1.88G / 1.25G used, `rpool` 920G / 176G used, both ONLINE |

**Notable containers:**
- `swag` (LinuxServer.io SWAG) — primary reverse proxy
- `authelia` + `authelia-mariadb` + `authelia-redis`
- `adguard` — DNS + ad blocking
- `gotify`
- `overseerr`
- `paperless` + `paperless-db` + `paperless-cache`
- `mcp-oauth` + `callback-relay` + `mcp-oauth-redis` — OAuth 2.1 for MCP servers
- `swag-mcp` — MCP for SWAG management
- `vaultwarden`, `linkding`, `karakeep`, `opengist`, `bytestash`
- `memos`, `radicale`, `searxng` + redis, `wizarr`
- `dockge`, `dozzle`, `rustdesk`, `multi-scrobbler`, `maloja`
- `dolt`, `onecli-postgres-1`, `portainer_agent`
- `arcane-agent` (v1.19.4)

---

### shart — Backup Target

Pure storage. ZFS receive endpoint.

| Property | Value |
|---|---|
| Role | ZFS backup target (Sanoid/Syncoid) |
| IP | `10.1.0.3` (LAN) / `100.118.209.1` (TS); also `169.254.80.235` on `shim-br0` |
| Hostname | `SHART` |
| OS | Unraid |
| CPU | 8 cores |
| RAM | 15.8 GB total |
| Uptime | 1d 19h |
| Containers | 3 running |
| Live CPU | not refreshed |
| Live RAM | 3.2 GiB / 15 GiB used |

**Storage:**
- Boot: `/dev/sda1` — 29 GB
- NVMe cache: `/dev/nvme0n1p1` — 239 GB (6.5 GB used)
- ZFS pool **`backup`**: **7.27 TB** total, 1.80 TB used, 5.47 TB free, frag 20%, ONLINE

shart receives ZFS streams nightly from both `tootie` (cache/*) and `squirts` (rpool/*). Holds full appdata/compose backups.

---

### steamy — GPU Workloads

Win11 host with WSL2 for GPU container workloads.

| Property | Value |
|---|---|
| Role | GPU compute (RTX 4070) |
| IP | `10.1.0.65` |
| Hostname | `STEAMY` (Windows) / `steamy-wsl` (WSL2) |
| OS | Windows 11 + WSL2 (Ubuntu) |
| GPU | NVIDIA RTX 4070 |
| Containers | 1 (in WSL Docker) |

**Notable container:** `crawl4r-qdrant` running `qdrant:gpu-nvidia-latest` — GPU-accelerated vector store, separate from dookie's CPU-bound `axon-qdrant`.

Arcane currently lists the `steamy` environment as disabled/offline, but SSH to `steamy-wsl` works and the GPU Qdrant container is running.

**This is also Jacob's actual desktop** — the `screenshots`, `clipboard`, `nircmd`, and `chrome` skills default to `ssh steamy-wsl`.

---

### vivobook — WSL Dev Machine

Laptop. Mobile development.

| Property | Value |
|---|---|
| Role | Mobile dev (WSL2) |
| IP | `10.1.0.5` (wired when docked) |
| Hostname | `vivobook-wsl` |
| OS | Windows 11 + WSL2 |
| Containers | 1 (arcane-agent) |
| Tailscale IP | `100.104.50.17` |

Notable: runs `arcane-agent` v1.19.4 in WSL2.

---

## Storage Architecture

### tootie — Unraid Array (Spinning Rust)

⚠ **CRITICAL: Array is running with ZERO parity.**

| Slot | Size | Model | Used | Notes |
|---|---|---|---|---|
| disk1 | 12 TB | WD Red | 90.9% | |
| disk2 | 12 TB | WD Red | 90.8% | |
| disk3 | 18 TB | WD Gold | 93.8% | high |
| disk4 | 14 TB | WD 140 | 92.0% | |
| disk5 | 18 TB | WD Gold | 93.7% | high |
| disk6 | 18 TB | WD Gold | 87.9% | |
| disk7 | 18 TB | WD Gold | 87.5% | |
| disk8 | 18 TB | WD Gold | 87.5% | |
| disk9 | 18 TB | WD Gold | 87.5% | |
| disk10 | 18 TB | WD Gold | 87.5% | |
| disk11 | 18 TB | WD Gold | 87.5% | |
| disk12 | 18 TB | WD Gold | 87.5% | |
| disk13 | 18 TB | WD Gold | 87.5% | |
| **TOTAL** | **~199 TiB mounted as `/mnt/user`** | | **182 TiB used / 17 TiB free (92%)** | |

**Last parity check:** 2025-01-03 (88 days ago, 0 errors, 101.8 MB/s, ~49h duration). At that time parity was configured. Parity disk is currently absent.

### tootie — ZFS Cache Pools (NVMe)

3 NVMe slots, each a separate ZFS pool.

| Pool | Device | Size | Used | Notes |
|---|---|---|---|---|
| `cache` | WD_BLACK SN7100 2TB | 5.45 TB (zfs report) | 1.85 TB (28%) | Primary cache, ZFS, ONLINE |
| `cache2` | Samsung 970 EVO Plus 2TB | — | ~0% | Spare / future use |
| `cache3` | Samsung 990 EVO Plus 2TB | — | ~0% | Spare / future use |

> Note: the "5.45 TB" size on `cache` exceeds the 2 TB physical drive — this suggests cache may be configured as a multi-device ZFS pool or includes compression accounting. Worth verifying.

### tootie — Unraid Shares (`/mnt/user/`)

| Share | Comment | Color | Cache |
|---|---|---|---|
| `3d` | GCodes, Models, Projects | green | — |
| `appdata` | application data | green | — |
| `archive` | archived code & session logs | green | — |
| `backups` | primary homelab backup target | **yellow** (high util) | — |
| `bin` | — | green | — |
| `code` | Code Repositories | green | — |
| `code-server` | code-server dev env | green | — |
| `compose` | production docker compose projects | green | — |
| `data` | apps, audio, books, comics, movies, music, tv | **yellow** | — |
| `docs` | homelab log & documentation | green | — |
| `domains` | VM images | green | — |
| `downloads` | Synced device downloads | green | — |
| `games` | PC games, ROMs & emulation | **yellow** | — |
| `isos` | "4real linux isos" | green | — |
| `photos` | immich libraries | green | — |
| `playbooks` | ansible playbooks | green | — |
| `system` | docker & libvirt | green | — |
| `workspace` | projects in development | green | — |

### tootie — Notable ZFS Datasets

Heavy hitters on `cache/` (in `/mnt/cache/`):

| Dataset | Used | Notes |
|---|---|---|
| `cache/appdata/plex` | 660 GB | Plex metadata + cache |
| `cache/photos/library` | 94.6 GB | Immich photos |
| `cache/system` | 88.5 GB | Docker + libvirt |
| `cache/workspace` | 82.4 GB | Dev projects |
| `cache/workspace/reader` | 45.9 GB | "reader" project |
| `cache/compose/pulse` | 11.1 GB | autopulse project |
| `cache/compose/better-chatbot` | 2.16 GB | |
| `cache/domains/Home Assistant` | 12.7 GB | HA VM image |
| `cache/code-server` | 12.3 GB | code-server data |
| `cache/appdata/radarr` | 13.0 GB | |
| `cache/appdata/sonarr` | 12.2 GB | |
| `cache/appdata/sabnzbd` | 9.15 GB | |
| `cache/workspace/hive` | 17.3 GB | hive project |
| `cache/workspace/nugget` | 10.3 GB | nugget project |

### shart — Backup Pool

| Pool | Size | Used | Frag | Health |
|---|---|---|---|---|
| `backup` | 7.27 TB | 1.80 TB | 20% | ONLINE |

Holds backup targets at:
- `backup/tootie/cache_*` (every tootie dataset replicated)
- `backup/squirts/rpool_*` (compose + appdata)

### squirts — ZFS

| Pool | Size | Used | Health |
|---|---|---|---|
| `bpool` | 1.88 GB | 1.25 GB | ONLINE |
| `rpool` | 920 GB | 176 GB | ONLINE |

---

## Backup Strategy

**Stack:** Sanoid (snapshots) + Syncoid (ZFS send/receive)

**Schedule:** Nightly snapshot + replication. Last successful run was not reverified during the 2026-05-22 refresh; the previous live sweep saw success messages for **2026-03-30 04:00-04:10 AM**.

### Replication Chains

| Source | Target | Datasets |
|---|---|---|
| `tootie` (Unraid) | `shart` | `cache/appdata`, `cache/compose`, `cache/workspace`, `cache/photos`, `cache/domains`, `cache/code-server`, `cache/code`, `cache/docs`, `cache/archive`, `cache/bin`, `cache/3d`, `cache/downloads`, `cache/playbooks` |
| `squirts` | `shart` | `rpool/compose/*`, `rpool/appdata/*` |

The March sweep reported clean recent Sanoid + Syncoid success messages via Gotify. Refresh backup job logs before relying on current backup health.

### Backup Strengths
- True ZFS send/receive (not rsync) — atomic, fast, snapshot-aware
- Off-host replication target (shart) physically separate
- Daily snapshots with retention via Sanoid

### Backup Gaps
- No off-site replication (everything is on-LAN)
- shart has a normal LAN address (`10.1.0.3`) plus the old link-local `169.254.80.235` on `shim-br0`; document which path Syncoid actually uses.

---

## Reverse Proxy & Public Services

**SWAG** (LinuxServer.io) on `squirts` — **149 active proxy configs** as of 2026-05-22.

All services are exposed via `*.tootie.tv` subdomains, fronted by **Authelia** for authentication.

### Sample exposed services (incomplete — 149 total)

**Media:**
`plex`, `sonarr`, `radarr`, `prowlarr`, `bazarr`, `overseerr`, `tautulli`, `sabnzbd`, `qbittorrent`, `audiobookshelf`, `kavita`, `navidrome`, `feishin`, `immich`, `wrapperr`, `popcorn`

**AI / RAG:**
`axon`, `neo4j`, `neo4j-memory`, `tei`, `ollama`, `qdrant`, `rag`, `optimus`, `agents`, `ngent`, `better-chatbot`, `nugget`, `promptstash`, `context-forge`

**MCP:**
`synapse`, `syslog-mcp`, `swag-mcp`, `mcp-auth`, `mcpx`

**Infrastructure:**
`portainer`, `code-server`, `firefox`, `dockge`, `dozzle`, `glances`, `scrutiny`, `vnstat`, `homarr`, `crontab-ui`, `olivetin`, `lab`, `unraid`, `tailscale`, `unifi`

**Productivity:**
`vaultwarden`, `joplin`, `linkding`, `karakeep`, `freshrss`, `paperless`, `memos`, `radicale`, `homebox`, `bytestash`, `opengist`

**Storage / Files:**
`minio`, `zipline`, `syncthing`, `filebrowser`, `filestash`

**Custom/business:**
`scbdb` (likely THC-Intel related), `taboot`

### Authentication: Authelia

- Backed by MariaDB + Redis (both on squirts)
- Fronts most internal services via `auth_request` directive in SWAG configs
- Default policy: 2FA required for sensitive services

---

## Service Catalog

### Media Stack (tootie)

| Service | Purpose | Notes |
|---|---|---|
| Plex | Media server | 660 GB appdata, nightly Tautulli reports |
| Sonarr | TV automation | nightly tag |
| Radarr | Movie automation | nightly tag |
| Bazarr | Subtitles | |
| Prowlarr | Indexer aggregator | |
| Sabnzbd | Usenet downloader | 9.15 GB appdata |
| qBittorrent | Torrent client | |
| Tautulli | Plex analytics | |
| Audiobookshelf | Audiobook server | |
| Kavita | Comics/manga server | |
| Navidrome | Music server | 3.10 GB |
| Feishin | Navidrome web client | |
| Wrapperr | Plex Wrapped year-in-review | |
| Plex-TVTime | Sync watch history | |
| Autopulse | Plex/Sonarr/Radarr scan automation | + postgres |
| Tracearr | Plex viewing analytics | |
| Shelfmark | Reading tracker | |
| Immich | Photo backup (94.6 GB library) | + postgres + redis + ML cache |

### Databases & Caches

| Service | Where | Notes |
|---|---|---|
| Postgres 14 | tootie | 138 MB |
| Postgres 15 | tootie | 92.6 MB |
| Postgres 16 | (referenced) | |
| Postgres 17 | tootie (`arcane_postgres`) | dookie Axon stack currently does not expose a Postgres container |
| MariaDB | tootie | |
| MySQL | tootie | |
| Redis (multiple) | tootie + squirts | |
| TimescaleDB | tootie (hive + tracearr) | |
| Neo4j 2025.10.1 | tootie (pulse_neo4j) | + axon neo4j |
| Qdrant 1.13.1 | dookie (axon) + steamy (GPU) | |
| MinIO | tootie | S3-compatible object store |
| Elasticsearch | squirts (historical syslog-ng stack) | not observed in 2026-05-22 `docker ps` |

### Infrastructure

| Service | Where | Notes |
|---|---|---|
| Portainer | squirts + shart agents; public config exists | full server not observed on tootie in 2026-05-22 `docker ps` |
| Watchtower | tootie | historical; not observed in 2026-05-22 `docker ps` |
| Glances | tootie | System monitor |
| Scrutiny | tootie | SMART monitoring |
| Vnstat | tootie | Bandwidth tracking |
| Diskspeed | tootie | |
| AdGuard Home | squirts | DNS-level ad blocking |
| code-server | tootie | historical/public config; not observed in 2026-05-22 `docker ps` |
| Firefox | tootie | historical/public config; not observed in 2026-05-22 `docker ps` |
| sshwifty | tootie | public config; not observed in 2026-05-22 `docker ps` |
| Dockge | squirts | Compose UI |
| Dozzle | squirts | Container log viewer |
| Olivetin | tootie | Button-based scripts |
| Crontab UI | tootie | |
| Notifiarr | tootie | Discord notifier |
| Infisical | tootie | public config; not observed in 2026-05-22 `docker ps` |
| Homebox | tootie | public config; not observed in 2026-05-22 `docker ps` |
| Homarr | tootie | public config; not observed in 2026-05-22 `docker ps` |
| Loggifly | tootie | observed as `ghcr.io/clemcer/loggifly:v1.4.0` |
| Change Detection | tootie | public config; not observed in 2026-05-22 `docker ps` |
| Syncthing | tootie | public config; not observed in 2026-05-22 `docker ps` |
| Esphome | tootie | public config; not observed in 2026-05-22 `docker ps` |
| Apprise-API | tootie | Multi-target notifications |

### Productivity / Personal

| Service | Where |
|---|---|
| Joplin Server | tootie (+ postgres), historical/public config; not observed in 2026-05-22 `docker ps` |
| Vaultwarden | squirts |
| FreshRSS | squirts (+ postgres), historical/public config; not observed in 2026-05-22 `docker ps` |
| Linkding (bookmarks) | squirts |
| Karakeep | squirts |
| Memos | squirts |
| Paperless-ngx | squirts (+ postgres + AI) |
| Radicale (calendar) | squirts |
| Searxng | squirts |
| Bytestash (snippets) | squirts |
| Opengist | squirts |
| Wizarr | squirts |
| RustDesk | squirts |
| Multi-scrobbler | squirts |
| Maloja | squirts |

---

## AI / RAG / Agent Stack

### Axon — Knowledge / RAG System (dookie)

Network: `axon`

| Component | Image | Purpose |
|---|---|---|
| `axon` | axon:dev-runtime | Axon API/runtime on port 8001 |
| `axon-qdrant` | qdrant 1.13.1 | Vector store |
| `axon-tei` | HuggingFace TEI 89-1.9 | Embeddings: **Qwen/Qwen3-Embedding-0.6B** (float16) |
| `axon-chrome` | headless Chrome | Web scraping |

**Pipeline (per memory):** Spider.rs crawler (~120 pages/sec) → Qwen3-Embedding-0.6B (TEI) → Qdrant + Postgres + Neo4j → exposed via REST + MCP.

**Active corpora:** ACP, MCP, Claude Code documentation.

Historical issues from March/May sessions: `403: requires scope axon:write` on some ingest flows and occasional Axon health check failures via SWAG at `axon.tootie.tv`. Reverify before treating either as current.

### GPU Inference (steamy)

- `crawl4r-qdrant` using `qdrant:gpu-nvidia-latest` build — secondary GPU-accelerated vector store on RTX 4070

### Other AI / Agent Services

| Service | Where | Notes |
|---|---|---|
| `better-chatbot` | tootie | public config exists; not observed in 2026-05-22 `docker ps` |
| `cli-proxy-api` | tootie | Present as `eceasy/cli-proxy-api:latest`; previous CVE note should be revalidated before action |
| `mcp-oauth-gateway` | squirts | OAuth 2.1 for MCP servers (159 MB) |
| `mcphub` | tootie | MCP server registry (+ db, 19 MB) - not observed in 2026-05-22 `docker ps` |
| `mcp-context-forge` | tootie | public config exists; not observed in 2026-05-22 `docker ps` |
| Open WebUI | tootie | not observed in 2026-05-22 `docker ps` |
| Affine | tootie | public SWAG config exists; container not observed in 2026-05-22 tootie `docker ps` |

---

## MCP Server Ecosystem

Jacob's homelab is also an MCP server farm. Notable MCP servers:

| MCP Server | Host | Port | Notes |
|---|---|---|---|
| `synapse-mcp` | dookie | 3000 | Historical SSH relay + ACP adapter; not observed in 2026-05-22 dookie `docker ps` |
| `syslog-mcp` | dookie | 1514 (TCP/UDP), 3100 (HTTP) | Rust + SQLite + FTS5 |
| `arcane-mcp` | dookie | 44332 | Docker fleet management |
| `arcane-agent` | tootie, dookie, squirts, shart, steamy, vivobook | — | Per-node agent (manages compose projects) |
| `unraid-mcp` | dookie | 40010 | unRAID GraphQL bridge |
| `swag-mcp` | squirts | 8012 (localhost binding) | SWAG config management |
| `unifi-mcp` | dookie | 40030 | UniFi controller bridge |
| `gotify-mcp` | dookie | 40020 | Gotify bridge |
| `tailscale-mcp` | dookie | 40040 | Tailscale bridge |
| `apprise-mcp` | dookie | 40050 | Apprise bridge |
| `example-mcp` | dookie | 40060 | RMCP template/example |
| `overseerr-mcp` | squirts | — | Historical; not observed in 2026-05-22 `docker ps` |
| `chroma-mcp`, `qbittorrent-mcp`, `radarr-mcp`, `sonarr-mcp`, `prowlarr-mcp`, `tautulli-mcp`, `sabnzbd-mcp`, `plex-mcp`, `portainer-mcp`, `tubearchivist-mcp`, `shrimp-mcp`, `memory-bank-mcp`, `fastfs-mcp`, `yarr-mcp` | tootie | — | Various |

**Synapse architecture:** Rust/Axum ACP gateway exposing local agents over REST+SSE with an OpenAI-compatible shim. Bridges Claude Code, Codex CLI to remote/web clients.

**arcane-agent version drift:** resolved for observed agents. tootie, dookie, squirts, shart, steamy-wsl, and vivobook-wsl report Arcane Agent image version **v1.19.4** or matching latest digest in 2026-05-22 checks. Arcane still lists the `steamy` environment itself as disabled/offline.

---

## Monitoring & Notifications

### Syslog (Rust-based syslog-mcp on dookie)

- Centralized log collection across primary hosts
- Storage: SQLite + FTS5
- Runtime counters: **5.82M entries written** as of 2026-05-22T23:48Z
- Docker ingest: 89 active container streams across 3 Docker hosts
- Host table (current syslog DB): squirts 7.39M, tootie 2.20M, dookie 795K, vivobook 80.5K, shart/SHART 40.4K combined, STEAMY 1.5K, router 3
- Current top emitter is **squirts**, not dookie.

### Gotify (squirts) — 19 Notification Apps

`Sonarr`, `Radarr`, `Prowlarr`, `Tautulli`, `unRAID` (tootie), `unRAID-shart`, `Bazarr`, `Apprise`, `ChangeDetection`, `Rclone`, `Overseerr`, `ZFS`, `autopulse`, `Synapse`, `Loggifly`, `clawd`, `Shelfmark`, `Arcane`, `Tracearr`

Recent notification stream not refreshed on 2026-05-22. The March snapshot was clean and mostly Sanoid/Syncoid success messages.

### Unraid Notifications

Not refreshed on 2026-05-22. The March snapshot had 20+ unread INFO backup-related notifications.

---

## Virtual Machines

Running on tootie via libvirt/KVM:

| VM | State | UUID | Notes |
|---|---|---|---|
| `dookie` | **RUNNING** | `95dda7eb-dbde-b679-f68f-d9c322daca7c` | Production dev VM; SSH verified 2026-05-22 |
| `Discovery` | (image present, 3.60 GB) | — | |
| `Home Assistant` | SHUTOFF | `e80cdd76-345a-4445-ba38-b4458451e532` | 12.7 GB image |
| `steamy` | SHUTOFF | `8dce4b2f-8d26-742a-215a-dc9ab9add6ca` | (real `steamy` is bare-metal Win11) |
| `steamy-vnc` | SHUTOFF | `03613256-a3b9-9a5a-799f-93dc56cb4d45` | |
| `Ubuntu` | (image present, 202K) | — | |
| `testbed` | (image present, 128K) | — | |

---

## Security Posture

### Container Vulnerability Scan (via Arcane Trivy integration)

Not refreshed on 2026-05-22. The table below is the previous March snapshot and should be treated as stale until a new Arcane vulnerability summary is run.

| Node | Images | Critical | High | Medium | Low | Total |
|---|---|---|---|---|---|---|
| tootie | 62 | **185** | 3,019 | 15,429 | 4,119 | 22,884 |
| dookie | 15 | 16 | 204 | 443 | 741 | 1,417 |
| steamy | 5 | 10 | 106 | 410 | 345 | 879 |
| shart | — | — | — | — | — | — |
| squirts | — | — | — | — | — | — |
| **Total** | **82** | **211** | **3,329** | **16,282** | **5,205** | **25,180** |

**Previous highest-risk container:** `cli-proxy-api` on tootie. It is still running, but the vulnerability result was not refreshed on 2026-05-22.

### Authentication / Access

- All public-facing services behind SWAG + Authelia (2FA)
- Tailscale mesh for inter-node SSH access (no public SSH)
- SSH keys: ED25519 (`SHA256:1zMWu3LJd4ETzBOp7gV1Pdi4I3A2P5osYigv/LRCUxU` is the primary)
- Infisical for application secrets management

### Network Security

- AdGuard Home for DNS-level filtering on `WillyNet`
- WPA2-PSK for WiFi (consider WPA3 transition)
- No exposed inbound ports except via SWAG → Authelia gate

---

## Known Issues & Tech Debt

### 🔴 Critical

1. **NO PARITY DISK on tootie array.** `mdcmd status` shows empty parity slots and `mdNumDisabled=2`; 13 spinning data disks are mounted with zero parity. Any drive failure = permanent data loss for that disk's content. **Action:** Add an 18TB+ parity disk ASAP. Cost ~$300.

2. **tootie array at 92% utilization (182 / 199 TiB).** Disks were not individually usage-refreshed, but the array-level pressure is worse than the March 89% snapshot. **Action:** Expand or prune `data` share (largest consumer).

3. **`cli-proxy-api` container on tootie still present.** It is now `eceasy/cli-proxy-api:latest` and has been up 2 days; rerun vulnerability scan to confirm whether the prior critical CVE finding still applies. **Action:** Update/remove if scan remains critical.

### 🟡 Warnings

4. **Arcane marks `steamy` disabled/offline.** SSH to `steamy-wsl` works and `crawl4r-qdrant` is running, but Arcane environment status is disabled/offline. **Action:** Re-register or intentionally document why Arcane does not manage the GPU box.

5. **shart still has link-local `169.254.80.235` even though LAN `10.1.0.3` is up.** Either intentional direct-interface history or leftover config. **Action:** Document the Syncoid target path and remove confusion.

6. **squirts RAM pressure remains meaningful.** Current sample shows 10 GiB / 14 GiB used while running 37 containers. **Action:** Watch memory and consider migrating heavier services if swap or OOM events appear.

7. **Axon health through SWAG has had prior failures at `axon.tootie.tv`.** Not reproduced in this refresh. **Action:** Reverify before changing SWAG/Axon config.

8. **Axon `403: requires scope axon:write`** when ingesting OpenAI Codex repo. **Action:** Audit OAuth scopes on `mcp-oauth-gateway`.

9. **Parity check history is stale while no parity disk is assigned.** Schedule monthly parity checks once a disk is added.

10. **Syslog hostname pollution.** Recent entries show malformed hostnames (`dook`, `dooki`, `doo`, `do`, `d`) from debugging — these are noise in the FTS index.

### 🟢 Nice-to-haves

11. **No off-site backup.** shart is on-LAN. Consider Backblaze B2 / rclone for irreplaceable data (photos, code).
12. **Cache pools 2 + 3 (Samsung 970 + 990) appear empty.** Could be used for additional services or moved to RAID for cache redundancy.
13. **5 SHUTOFF VMs taking up domain image space.** Cull unused VM images.
14. **`cache/archive/*` has dozens of micro-datasets (mostly 128K each) from old MCP project experiments.** Worth pruning to reduce dataset count and snapshot overhead.

---

## Appendix: Key URLs

### Internal (LAN / Tailscale)

| Service | URL |
|---|---|
| Unraid Web UI | http://10.1.0.2:6969 |
| Synapse MCP | http://dookie:3000 (historical; not observed in 2026-05-22 `docker ps`) |
| Syslog MCP | http://dookie:3100 |
| Arcane UI | http://10.1.0.2:3552 / https://arcane.tootie.tv |
| Arcane MCP | http://dookie:44332 |
| Unraid MCP | http://dookie:40010 |
| Plex | http://10.1.0.2:32400 |
| Portainer | http://10.1.0.2:9000 (historical/public config; server not observed in 2026-05-22 tootie `docker ps`) |
| Glances | http://10.1.0.2:61208 |
| Scrutiny | http://10.1.0.2:8080 |
| Windows sandbox (winbox/noVNC) | http://dookie:8006 |
| Windows sandbox (RDP) | dookie:33890 |

### Public (via SWAG -> Authelia)

Format: `https://<service>.tootie.tv`

All 149 active SWAG configs follow this pattern. Notable examples:
- `https://plex.tootie.tv`
- `https://overseerr.tootie.tv`
- `https://immich.tootie.tv`
- `https://axon.tootie.tv` (⚠ health check failing)
- `https://synapse.tootie.tv`
- `https://agents.tootie.tv`
- `https://better-chatbot.tootie.tv`

---

*Document generated from live MCP introspection of Arcane, SWAG, Syslog, and SSH host checks. Some March 2026 sections remain intentionally marked as stale where the live endpoint failed or where a safe refresh was not performed.*
