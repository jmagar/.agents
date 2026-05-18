# WillyNet Homelab — Infrastructure Documentation

> Seeded from live MCP sweep · 2026-03-31
> Owner: Jacob Magar (jmagar) · Columbia, SC

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
| Total containers running | ~104 fleet-wide |
| Total storage capacity | ~210 TB (unRAID array) + ~14 TB (ZFS) + ~6 TB NVMe |
| Active SWAG proxy configs | 128 |
| Gotify notification apps | 19 |
| UniFi clients | 32 connected |
| Syslog volume | 3.9M entries (rolling, since 2026-03-28) |

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
- **No active UniFi alarms or events.**

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
| shart | `169.254.80.235` | **link-local** | ⚠ not getting DHCP — see Known Issues |

### Tailscale IPs (selected)

| Host | Tailscale IP |
|---|---|
| dookie | `100.88.16.79` |
| tootie | `100.120.242.29` (ssh port 29229) |

### Wireless Clients (26 connected)

Notable: 2× Nest Audio, Google Home Mini, Google Nest Mini, Chromecast Audio, Living Room TV, Nursery Camera + Light, multiple ESPHome smart lights (bedroom, dining, living room, stove), Wyze Cam.

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
| RAM | 64 GB DDR4-3200 (4× Corsair CMK64GX4M2E3200C16) — actually reports 128 GB total via Unraid GraphQL |
| Motherboard | MSI PRO Z790-A WIFI DDR4 |
| Web UI | http://10.1.0.2:6969 (HTTP) / :31337 (HTTPS) |
| SSH | port 29229 |
| Uptime | since 2026-03-28 |
| Containers | ~65 running |
| Live CPU | ~13.8% (thread 9 pegged, threads 10–11 ~25–31%) |
| Live RAM | 68.6% (89 GB / 128 GB) — 0 swap used |

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
| Uptime | 1d 3h |
| Containers | 15 running |
| Live CPU | ~3.2% |
| Live RAM | 58.3% (34.5 / 59 GB) |
| Load avg | 0.71 / 0.90 / 1.06 |

**Note:** dookie is a VM running on tootie (state: `RUNNING` in libvirt). It's also reachable directly over the LAN as `10.1.0.6`.

**Notable containers on dookie:**
- `axon-qdrant` (v1.13.1) — vector store
- `axon-tei` — HuggingFace TEI serving **Qwen3-Embedding-0.6B** (float16)
- `axon-ollama` (v0.6.5)
- `axon-rabbitmq` (4.0-management)
- `axon-postgres` (pg17-alpine)
- `axon-redis` (8.2-alpine)
- `axon-chrome` — headless Chrome for scraping
- `axon-mem0` — FastAPI mem0 service
- `pulse_neo4j` — neo4j:2025.10.1-community
- `synapse-mcp` — Node.js, port 3000
- `syslog-mcp` — Rust binary, ports 1514 (TCP/UDP) + 3100 (HTTP)
- `arcane-mcp` — port 44332
- `unraid-mcp` — port 6970
- `arcane-agent` (v1.16.4) — manages `/home/jmagar/compose`
- `dockersocket` proxy (Tecnativa)
- `windows` (dockur/windows) — Windows 11 sandbox at `:8006` (noVNC), `:33890` (RDP). This is the **winbox** skill target.

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
| Uptime | 5d 6h |
| Containers | 18 running |
| Live CPU | ~2.3% |
| Live RAM | 84.3% (12.8 / 15 GB) — ⚠ high |
| ZFS | `bpool` (1.88 GB, 35% used) + `rpool` (920 GB, 14% used) |

**Notable containers:**
- `swag` (LinuxServer.io SWAG) — primary reverse proxy
- `authelia` + `authelia-mariadb` + `authelia-redis`
- `adguard` — DNS + ad blocking
- `gotify` + `gotify-mcp`
- `overseerr` + `overseerr-mcp`
- `paperless` + `paperless-db` + `paperless-ai`
- `mcp-oauth-gateway` — OAuth 2.1 for MCP servers
- `swag-mcp` — MCP for SWAG management
- `agentsview` — `ghcr.io/jmagar/agentsview`
- `unifi-mcp`, `syslog-ng` + `syslog-ng_elasticsearch`
- `vaultwarden`, `linkding`, `karakeep`, `freshrss` + postgres, `opengist`
- `memos`, `radicale`, `searxng` + redis, `wizarr`
- `dockge`, `dozzle`, `rustdesk`, `multi-scrobbler`, `maloja`
- `arcane-agent` (v1.11.2 — **outdated**)

---

### shart — Backup Target

Pure storage. ZFS receive endpoint.

| Property | Value |
|---|---|
| Role | ZFS backup target (Sanoid/Syncoid) |
| IP | `169.254.80.235` ⚠ link-local (see Known Issues) |
| Hostname | `SHART` |
| OS | Unraid |
| CPU | 8 cores |
| RAM | 15.8 GB total |
| Uptime | 25d 8h |
| Containers | 3 running |
| Live CPU | ~2.2% |
| Live RAM | 28.4% (4.5 / 15.8 GB) |

**Storage:**
- Boot: `/dev/sda1` — 29 GB
- NVMe cache: `/dev/nvme0n1p1` — 239 GB (6.5 GB used)
- ZFS pool **`backup`**: **7.27 TB** total, 1.74 TB used (23%), frag 19%, ONLINE

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
| Containers | 2 (in WSL Docker) |

**Notable container:** `crawl4r-qdrant` running `qdrant:gpu-nvidia-latest` — GPU-accelerated vector store, separate from dookie's CPU-bound `axon-qdrant`.

Also runs `arcane-agent` v1.16.4.

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

Notable: chattiest syslog client after dookie (~101K logs in current window).

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
| **TOTAL** | **~203 TB** | | **89% used** | |

**Last parity check:** 2025-01-03 (88 days ago, 0 errors, 101.8 MB/s, ~49h duration). At that time parity was configured. Parity disk is currently absent.

### tootie — ZFS Cache Pools (NVMe)

3 NVMe slots, each a separate ZFS pool.

| Pool | Device | Size | Used | Notes |
|---|---|---|---|---|
| `cache` | WD_BLACK SN7100 2TB | 5.45 TB (zfs report) | 1.69 TB (30%) | Primary cache, ZFS, frag 27%, ONLINE |
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
| `backup` | 7.27 TB | 1.74 TB (23%) | 19% | ONLINE |

Holds backup targets at:
- `backup/tootie/cache_*` (every tootie dataset replicated)
- `backup/squirts/rpool_*` (compose + appdata)

### squirts — ZFS

| Pool | Size | Used | Health |
|---|---|---|---|
| `bpool` | 1.88 GB | 35% | ONLINE |
| `rpool` | 920 GB | 14% (133 GB) | ONLINE |

---

## Backup Strategy

**Stack:** Sanoid (snapshots) + Syncoid (ZFS send/receive)

**Schedule:** Nightly snapshot + replication. Last successful run logged at **2026-03-30 04:00–04:10 AM**.

### Replication Chains

| Source | Target | Datasets |
|---|---|---|
| `tootie` (Unraid) | `shart` | `cache/appdata`, `cache/compose`, `cache/workspace`, `cache/photos`, `cache/domains`, `cache/code-server`, `cache/code`, `cache/docs`, `cache/archive`, `cache/bin`, `cache/3d`, `cache/downloads`, `cache/playbooks` |
| `squirts` | `shart` | `rpool/compose/*`, `rpool/appdata/*` |

All recent Sanoid + Syncoid runs reported success via Gotify. No backup failures in the rolling notification window.

### Backup Strengths
- True ZFS send/receive (not rsync) — atomic, fast, snapshot-aware
- Off-host replication target (shart) physically separate
- Daily snapshots with retention via Sanoid

### Backup Gaps
- No off-site replication (everything is on-LAN)
- shart's link-local IP means replication is happening over an unconfigured network path — verify it's via direct interface, not failing back to mDNS

---

## Reverse Proxy & Public Services

**SWAG** (LinuxServer.io) on `squirts` — **128 active proxy configs**.

All services are exposed via `*.tootie.tv` subdomains, fronted by **Authelia** for authentication.

### Sample exposed services (incomplete — 128 total)

**Media:**
`plex`, `sonarr`, `radarr`, `prowlarr`, `bazarr`, `overseerr`, `tautulli`, `sabnzbd`, `qbittorrent`, `audiobookshelf`, `kavita`, `navidrome`, `feishin`, `immich`, `wrapperr`, `popcorn`

**AI / RAG:**
`axon`, `neo4j`, `neo4j-memory`, `tei`, `ollama`, `qdrant`, `rag`, `optimus`, `agents`, `ngent`, `agentsview`, `better-chatbot`, `nugget`, `promptstash`, `context-forge`

**MCP:**
`synapse`, `syslog-mcp`, `swag-mcp`, `mcp-auth`, `mcpx`

**Infrastructure:**
`portainer`, `code-server`, `firefox`, `dockge`, `dozzle`, `glances`, `scrutiny`, `vnstat`, `homarr`, `crontab-ui`, `olivetin`

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
| Postgres 17 | tootie (axon stack) | |
| MariaDB | tootie | |
| MySQL | tootie | |
| Redis (multiple) | tootie + squirts | |
| TimescaleDB | tootie (hive + tracearr) | |
| Neo4j 2025.10.1 | tootie (pulse_neo4j) | + axon neo4j |
| Qdrant 1.13.1 | dookie (axon) + steamy (GPU) | |
| MinIO | tootie | S3-compatible object store |
| Elasticsearch | squirts (for syslog-ng) | 13 GB |

### Infrastructure

| Service | Where | Notes |
|---|---|---|
| Portainer EE (STS) | tootie | |
| Watchtower | tootie | Auto-updates |
| Glances | tootie | System monitor |
| Scrutiny | tootie | SMART monitoring |
| Vnstat | tootie | Bandwidth tracking |
| Diskspeed | tootie | |
| AdGuard Home | squirts | DNS-level ad blocking |
| code-server | tootie | Web IDE, 12.3 GB |
| Firefox | tootie | Containerized browser |
| sshwifty | tootie | Web SSH |
| Dockge | squirts | Compose UI |
| Dozzle | squirts | Container log viewer |
| Olivetin | tootie | Button-based scripts |
| Crontab UI | tootie | |
| Notifiarr | tootie | Discord notifier |
| Infisical | tootie | Secrets management (+ postgres + redis) |
| Homebox | tootie | Inventory tracker |
| Homarr | tootie | Dashboard |
| Loggifly | (TBD) | Log aggregation |
| Change Detection | tootie | URL diff monitor |
| Syncthing | tootie | File sync |
| Esphome | tootie | ESP32 device config |
| Apprise-API | tootie | Multi-target notifications |

### Productivity / Personal

| Service | Where |
|---|---|
| Joplin Server | tootie (+ postgres) |
| Vaultwarden | squirts |
| FreshRSS | squirts (+ postgres) |
| Linkding (bookmarks) | squirts |
| Karakeep | squirts |
| Memos | squirts |
| Paperless-ngx | squirts (+ postgres + AI) |
| Radicale (calendar) | squirts |
| Searxng | squirts |
| Bytestash (snippets) | tootie |
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
| `axon-qdrant` | qdrant 1.13.1 | Vector store |
| `axon-tei` | HuggingFace TEI | Embeddings: **Qwen3-Embedding-0.6B** (float16) |
| `axon-ollama` | Ollama 0.6.5 | Local LLM inference |
| `axon-rabbitmq` | 4.0-management | Job queue |
| `axon-postgres` | pg17-alpine | Metadata store |
| `axon-redis` | redis 8.2-alpine | Cache |
| `axon-chrome` | headless Chrome | Web scraping |
| `axon-mem0` | FastAPI mem0 | Long-term memory |
| `pulse_neo4j` | neo4j 2025.10.1 | Knowledge graph |

**Pipeline (per memory):** Spider.rs crawler (~120 pages/sec) → Qwen3-Embedding-0.6B (TEI) → Qdrant + Postgres + Neo4j → exposed via REST + MCP.

**Active corpora:** ACP, MCP, Claude Code documentation.

**Recent issue:** `403: requires scope axon:write` when ingesting OpenAI Codex GitHub repo.
**Recent issue:** Axon health check failures via SWAG at `axon.tootie.tv`.

### GPU Inference (steamy)

- `crawl4r-qdrant` using `qdrant:gpu-nvidia-latest` build — secondary GPU-accelerated vector store on RTX 4070

### Other AI / Agent Services

| Service | Where | Notes |
|---|---|---|
| `better-chatbot` | tootie | Multi-provider chat UI (+ postgres + redis) |
| `agentsview` | squirts | Custom Claude/Codex session viewer (`ghcr.io/jmagar/agentsview`) — mounts Claude and Codex creds |
| `cli-proxy-api` | tootie | ⚠ pinned SHA256 with critical CVEs (see Known Issues) |
| `mcp-oauth-gateway` | squirts | OAuth 2.1 for MCP servers (159 MB) |
| `mcphub` | tootie | MCP server registry (+ db, 19 MB) |
| `mcp-context-forge` | tootie | Context engineering tooling |
| Open WebUI | tootie | (+ redis cache, 4.8 GB) |
| Affine | tootie | Collaborative notes (+ db + redis + manticore search) |

---

## MCP Server Ecosystem

Jacob's homelab is also an MCP server farm. Notable MCP servers:

| MCP Server | Host | Port | Notes |
|---|---|---|---|
| `synapse-mcp` | dookie | 3000 | SSH relay + ACP adapter, primary gateway. Mounts `~/.ssh` + docker socket |
| `syslog-mcp` | dookie | 1514 (TCP/UDP), 3100 (HTTP) | Rust + SQLite + FTS5 |
| `arcane-mcp` | dookie | 44332 | Docker fleet management |
| `arcane-agent` | tootie, dookie, squirts, shart, steamy, vivobook | — | Per-node agent (manages compose projects) |
| `unraid-mcp` | dookie | 6970 | unRAID GraphQL bridge |
| `swag-mcp` | squirts | — | SWAG config management |
| `unifi-mcp` | squirts | — | UniFi controller bridge |
| `gotify-mcp` | squirts | — | Gotify bridge |
| `overseerr-mcp` | squirts | — | Overseerr bridge |
| `chroma-mcp`, `qbittorrent-mcp`, `radarr-mcp`, `sonarr-mcp`, `prowlarr-mcp`, `tautulli-mcp`, `sabnzbd-mcp`, `plex-mcp`, `portainer-mcp`, `tubearchivist-mcp`, `shrimp-mcp`, `memory-bank-mcp`, `fastfs-mcp`, `yarr-mcp` | tootie | — | Various |

**Synapse architecture:** Rust/Axum ACP gateway exposing local agents over REST+SSE with an OpenAI-compatible shim. Bridges Claude Code, Codex CLI to remote/web clients.

**arcane-agent version drift:** dookie + steamy on **v1.16.4** (current). tootie + squirts on **v1.11.2** (5 versions behind).

---

## Monitoring & Notifications

### Syslog (Rust-based syslog-mcp on dookie)

- Centralized log collection across 7 primary hosts
- Storage: SQLite + FTS5
- Volume: **3.9M entries** in rolling window (since 2026-03-28)
- DB size: 1.86 GB (max 10 GB)
- Top emitter: **dookie (~3.7M logs)** — by far the chattiest (Docker + MCP services)
- Other emitters: vivobook (~102K), steamy (~37K), squirts (~55K), shart (~20K), tootie (~17K)

### Gotify (squirts) — 19 Notification Apps

`Sonarr`, `Radarr`, `Prowlarr`, `Tautulli`, `unRAID` (tootie), `unRAID-shart`, `Bazarr`, `Apprise`, `ChangeDetection`, `Rclone`, `Overseerr`, `ZFS`, `autopulse`, `Synapse`, `Loggifly`, `clawd`, `Shelfmark`, `Arcane`, `Tracearr`

Recent notification stream: clean. All entries are Sanoid snapshot + Syncoid replication success messages.

### Unraid Notifications

20+ recent UNREAD notifications, all `INFO` severity, all backup-related (ZFS snapshot + replication successes from 2026-03-30 04:00–04:10 AM window).

---

## Virtual Machines

Running on tootie via libvirt/KVM:

| VM | State | UUID | Notes |
|---|---|---|---|
| `dookie` | **RUNNING** | `95dda7eb-dbde-b679-f68f-d9c322daca7c` | Production dev VM |
| `Discovery` | (image present, 3.60 GB) | — | |
| `Home Assistant` | SHUTOFF | `e80cdd76-345a-4445-ba38-b4458451e532` | 12.7 GB image |
| `steamy` | SHUTOFF | `8dce4b2f-8d26-742a-215a-dc9ab9add6ca` | (real `steamy` is bare-metal Win11) |
| `steamy-vnc` | SHUTOFF | `03613256-a3b9-9a5a-799f-93dc56cb4d45` | |
| `Ubuntu` | (image present, 202K) | — | |
| `testbed` | (image present, 128K) | — | |

---

## Security Posture

### Container Vulnerability Scan (via Arcane Trivy integration)

| Node | Images | Critical | High | Medium | Low | Total |
|---|---|---|---|---|---|---|
| tootie | 62 | **185** | 3,019 | 15,429 | 4,119 | 22,884 |
| dookie | 15 | 16 | 204 | 443 | 741 | 1,417 |
| steamy | 5 | 10 | 106 | 410 | 345 | 879 |
| shart | — | — | — | — | — | — |
| squirts | — | — | — | — | — | — |
| **Total** | **82** | **211** | **3,329** | **16,282** | **5,205** | **25,180** |

**Highest-risk container:** `cli-proxy-api` on tootie — pinned SHA256 image with known critical CVEs.

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

1. **NO PARITY DISK on tootie array.** 13 spinning disks at 89% utilization with zero redundancy. Last successful parity check: 2025-01-03. Any drive failure = permanent data loss for that disk's content. **Action:** Add an 18TB+ parity disk ASAP. Cost ~$300.

2. **tootie array at 89% utilization (181 / 203 TB).** Disks 3 and 5 specifically at 93%+ which can cause filesystem performance degradation. **Action:** Expand or prune `data` share (largest consumer).

3. **`cli-proxy-api` container on tootie running with critical CVEs.** Pinned SHA256 image, has been up 3+ days. **Action:** Update to current image or remove if obsolete.

### 🟡 Warnings

4. **`arcane-agent` version drift.** tootie + squirts on v1.11.2; dookie + steamy on v1.16.4 (5 versions ahead). **Action:** Update tootie and squirts.

5. **shart on link-local IP (169.254.80.235).** Either intentional (direct ZFS replication interface) or broken DHCP. **Action:** Verify and document.

6. **squirts RAM at 84.3%.** Limited headroom on a 15 GB box running 18 containers. **Action:** Consider migrating heavier services (Elasticsearch?) or upgrading RAM.

7. **Axon health check failing via SWAG at `axon.tootie.tv`.** **Action:** Investigate health endpoint config in SWAG vhost.

8. **Axon `403: requires scope axon:write`** when ingesting OpenAI Codex repo. **Action:** Audit OAuth scopes on `mcp-oauth-gateway`.

9. **Last parity check was 88 days ago.** Even though there's no parity disk currently, this is the historical record. Schedule monthly parity checks once a disk is added.

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
| Synapse MCP | http://dookie:3000 |
| Syslog MCP | http://dookie:3100 |
| Arcane | http://10.1.0.2:44332 |
| Unraid MCP | http://dookie:6970 |
| Plex | http://10.1.0.2:32400 |
| Portainer | http://10.1.0.2:9000 |
| Glances | http://10.1.0.2:61208 |
| Scrutiny | http://10.1.0.2:8080 |
| Windows sandbox (winbox/noVNC) | http://dookie:8006 |
| Windows sandbox (RDP) | dookie:33890 |

### Public (via SWAG → Authelia)

Format: `https://<service>.tootie.tv`

All 128 SWAG configs follow this pattern. Notable examples:
- `https://plex.tootie.tv`
- `https://overseerr.tootie.tv`
- `https://immich.tootie.tv`
- `https://axon.tootie.tv` (⚠ health check failing)
- `https://synapse.tootie.tv`
- `https://agents.tootie.tv`
- `https://better-chatbot.tootie.tv`

---

*Document generated from live MCP introspection of Arcane, Gotify, Overseerr, SWAG, Synapse, Syslog, Unifi, and unRAID servers. Some details (mostly per-container metadata and full SWAG vhost listings) were summarized rather than enumerated exhaustively.*
