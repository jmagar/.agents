# WillyNet Homelab - Infrastructure Documentation

> Generated: 2026-05-22 21:44:06 EDT
> Generator: `src/skills/homelab-map/scripts/generate-homelab-report.py`
> Collection method: non-interactive SSH, Docker CLI, ZFS CLI, Unraid shell commands, and SWAG config files.

---

## Overview

| Metric | Value |
|---|---|
| Total nodes | 6 |
| Total containers running | 110 |
| Active SWAG proxy configs | 149 |
| Network | WillyNet / 10.1.0.0/24 plus Tailscale mesh |
| Primary public domain | *.tootie.tv via SWAG on squirts |

## Collection Notes

- All configured host collection commands completed successfully.

Values in this document are a fresh runtime snapshot. Re-run the generator before making operational decisions:

```bash
python3 src/skills/homelab-map/scripts/generate-homelab-report.py
```

## Nodes

| Name | Role | LAN IP | Tailscale IP | OS | Kernel | Uptime | Memory | Containers |
|---|---|---|---|---|---|---|---|---|
| tootie | Primary NAS / app server | 10.1.0.2 | 100.120.242.29 | Unraid | Linux 6.12.54-Unraid | up 3 weeks, 5 days, 14 hours, 38 minutes | 88Gi / 125Gi used | 49 |
| dookie | Dev / AI / MCP hub | 10.1.0.6 | 100.88.16.79 | Linux KVM guest on tootie | Linux 7.0.0-15-generic | up 2 days, 3 hours, 8 minutes | 41Gi / 57Gi used | 19 |
| squirts | Edge services | 10.1.0.8 | 100.75.111.118 | Ubuntu | Linux 6.17.0-29-generic | up 2 days, 3 hours, 35 minutes | 10Gi / 14Gi used | 37 |
| shart | ZFS backup target | 10.1.0.3 | 100.118.209.1 | Unraid | Linux 6.12.54-Unraid | up 1 day, 21 hours, 37 minutes | 3.2Gi / 15Gi used | 3 |
| steamy / steamy-wsl | GPU workloads | not observed | 100.74.16.82 | Windows 11 + WSL2 | Linux 5.15.167.4-microsoft-standard-WSL2 | up 1 day, 6 hours, 24 minutes | 2.0Gi / 30Gi used | 1 |
| vivobook / vivobook-wsl | Mobile dev laptop | 10.1.0.5 | 100.104.50.17 | Windows 11 + WSL2 | Linux 6.6.87.2-microsoft-standard-WSL2 | up 1 day, 3 hours, 30 minutes | 1.0Gi / 11Gi used | 1 |

### Network Interfaces

#### tootie
- `lo               UNKNOWN        127.0.0.1/8`
- `br0              UP             10.1.0.2/24 metric 1`
- `br-1c487b072bef  UP             172.19.0.1/16`
- `br-cab89702537c  UP             10.2.0.1/16`
- `docker0          DOWN           172.17.0.1/16`
- `tailscale1       UNKNOWN        100.120.242.29/32`
#### dookie
- `lo               UNKNOWN        127.0.0.1/8`
- `enp1s0           UP             10.1.0.6/24`
- `br-88626fc1d29b  UP             172.26.0.1/16`
- `br-9e72de829602  UP             172.25.0.1/16`
- `docker0          DOWN           172.17.0.1/16`
- `br-5605dfd09dcf  UP             172.19.0.1/16`
- `tailscale0       UNKNOWN        100.88.16.79/32`
- `br-7882f50f0b4c  UP             172.18.0.1/16`
- `br-815298847eba  UP             172.20.0.1/16`
#### squirts
- `lo               UNKNOWN        127.0.0.1/8`
- `enx00e04c680225  UP             10.1.0.8/24`
- `tailscale0       UNKNOWN        100.75.111.118/32`
- `br-2040b8105cb7  UP             172.20.0.1/16`
- `br-35bb6ab2bf39  UP             10.6.0.1/16`
- `docker0          UP             172.17.0.1/16`
#### shart
- `lo               UNKNOWN        127.0.0.1/8`
- `br0              UP             10.1.0.3/24`
- `tailscale1       UNKNOWN        100.118.209.1/32`
- `br-b20808aae73e  UP             10.5.0.1/16`
- `docker0          UP             172.17.0.1/16`
- `shim-br0@br0     UP             10.1.0.3/24 169.254.80.235/16 metric 1005`
#### steamy / steamy-wsl
- `lo               UNKNOWN        127.0.0.1/8 10.255.255.254/32`
- `eth0             UP             172.23.180.190/20`
- `tailscale0       UNKNOWN        100.74.16.82/32`
#### vivobook / vivobook-wsl
- `lo               UNKNOWN        127.0.0.1/8 10.255.255.254/32`
- `eth2             UP             100.112.100.103/32`
- `eth3             UP             10.1.0.5/24`
- `tailscale0       UNKNOWN        100.104.50.17/32`

## Service Location Summary

Observed means the expected container name was found in the live `docker ps` output for that host. Missing may mean the service moved, is stopped, has a different container name, or is only represented by a SWAG config.

| Host | Expected services observed | Expected services not observed |
|---|---|---|
| tootie | plex, sonarr, radarr, bazarr, prowlarr, qbittorrent, sabnzbd, tautulli, immich, audiobookshelf, kavita, navidrome, minio, loggifly, notifiarr, apprise-api, olivetin, zipline | - |
| dookie | axon, axon-qdrant, axon-tei, axon-chrome, syslog-mcp, arcane-mcp, unraid-mcp, gotify-mcp, unifi-mcp, tailscale-mcp, apprise-mcp, labby, agent-os-win11 | - |
| squirts | swag, authelia, adguard, gotify, vaultwarden, paperless, linkding, karakeep, bytestash, memos, radicale, searxng, dockge, dozzle, rustdesk, multi-scrobbler, maloja | - |
| shart | arcane-agent, portainer_agent, dockersocket | - |
| steamy / steamy-wsl | crawl4r-qdrant | arcane-agent |
| vivobook / vivobook-wsl | arcane-agent | - |

## Host Container Inventory

### tootie
| Container | Image | Ports | Status |
|---|---|---|---|
| adminer | 0959399eff12 | 0.0.0.0:1993->8080/tcp, [::]:1993->8080/tcp | Up 3 weeks |
| agregarr | agregarr/agregarr:latest | 0.0.0.0:52000->7171/tcp, [::]:52000->7171/tcp | Up 3 weeks |
| apprise-api | 278de85adde9 | 0.0.0.0:8766->8000/tcp, [::]:8766->8000/tcp | Up 2 weeks |
| arcane | ghcr.io/getarcaneapp/arcane:latest | 0.0.0.0:3552->3552/tcp, :::3552->3552/tcp | Up 4 days |
| arcane_postgres | postgres:17-alpine | 0.0.0.0:56000->5432/tcp, [::]:56000->5432/tcp | Up 7 days (healthy) |
| audiobookshelf | b1290bc75356 | 0.0.0.0:13378->80/tcp, [::]:13378->80/tcp | Up 3 weeks |
| autopulse | ghcr.io/dan-online/autopulse:latest | 0.0.0.0:2875->80/tcp, [::]:2875->80/tcp | Up 2 days (healthy) |
| autopulse-postgres | postgres:16 | 5432/tcp | Up 2 days (healthy) |
| bazarr | 88351f2190bf | 0.0.0.0:6767->6767/tcp, :::6767->6767/tcp | Up 12 days |
| cli-proxy-api | eceasy/cli-proxy-api:latest | 0.0.0.0:1455->1455/tcp, :::1455->1455/tcp, 0.0.0.0:8085->8085/tcp, :::8085->8085/tcp, 0.0.0.0:8317->8317/tcp, :::8317->8317/tcp, 0.0.0.0:11451->11451/tcp, :::11451->11451/tcp, 0.0.0.0:51121->51121/tcp, :::51121->51121/tcp, 0.0.0.0:54545->54545/tcp, :::54545->54545/tcp | Up 2 days |
| cli-proxy-postgres | postgres:16 | 0.0.0.0:5442->5432/tcp, [::]:5442->5432/tcp | Up 2 days (healthy) |
| crontab-ui | alseambusher/crontab-ui:latest | 8000/tcp, 0.0.0.0:8969->80/tcp, [::]:8969->80/tcp | Up 3 weeks (healthy) |
| diskspeed | jbartlett777/diskspeed:latest | 8080/tcp, 0.0.0.0:18888->80/tcp, [::]:18888->80/tcp | Up 3 weeks |
| dockersocket | ghcr.io/tecnativa/docker-socket-proxy:latest | 0.0.0.0:2375->2375/tcp, :::2375->2375/tcp | Up 3 weeks |
| feishin | ghcr.io/jeffvli/feishin:latest | 8080/tcp, 0.0.0.0:9180->9180/tcp, :::9180->9180/tcp | Up 3 weeks |
| flaresolverr | flaresolverr/flaresolverr:latest | 0.0.0.0:8191->8191/tcp, :::8191->8191/tcp, 8192/tcp | Up 3 weeks |
| glances | nicolargo/glances:latest | 0.0.0.0:61208->61208/tcp, :::61208->61208/tcp, 61209/tcp | Up 3 weeks |
| immich_machine_learning | ghcr.io/immich-app/immich-machine-learning:release | - | Up 3 weeks (healthy) |
| immich_postgres | tensorchord/pgvecto-rs:pg14-v0.2.0 | 5432/tcp | Up 3 weeks (healthy) |
| immich_redis | redis:6.2-alpine | 6379/tcp | Up 3 weeks (healthy) |
| immich_server | ghcr.io/immich-app/immich-server:release | 0.0.0.0:2283->2283/tcp, :::2283->2283/tcp | Up 3 weeks (healthy) |
| kavita | 481aea096079 | 5000/tcp, 0.0.0.0:5999->80/tcp, [::]:5999->80/tcp | Up 3 weeks (healthy) |
| loggifly | ghcr.io/clemcer/loggifly:v1.4.0 | - | Up 2 weeks (healthy) |
| mariadb | lscr.io/linuxserver/mariadb:latest | 0.0.0.0:3306->3306/tcp, :::3306->3306/tcp | Up 2 days |
| minio | minio/minio:latest | 0.0.0.0:9000-9001->9000-9001/tcp, :::9000-9001->9000-9001/tcp | Up 3 weeks (healthy) |
| navidrome | 50e167470f18 | 0.0.0.0:4533->4533/tcp, :::4533->4533/tcp | Up 3 weeks |
| notifiarr | golift/notifiarr:latest | 0.0.0.0:5454->5454/tcp, :::5454->5454/tcp | Up 3 weeks |
| olivetin | jamesread/olivetin:latest | 0.0.0.0:1337->1337/tcp, :::1337->1337/tcp | Up 22 hours |
| plex | 5809619fa0e3 | 1900/udp, 5353/udp, 32410/udp, 8324/tcp, 32412-32414/udp, 32469/tcp, 0.0.0.0:32400->32400/tcp, :::32400->32400/tcp | Up 3 weeks |
| plex-tvtime | zggis/plex-tvtime:latest | 4444/tcp, 9515/tcp, 0.0.0.0:3365->8080/tcp, [::]:3365->8080/tcp | Up 2 weeks |
| postgresql14 | 5707f60969a4 | 0.0.0.0:5432->5432/tcp, :::5432->5432/tcp | Up 12 days |
| postgresql15 | 86832d1a469e | 0.0.0.0:5433->5432/tcp, [::]:5433->5432/tcp | Up 13 days |
| prowlarr | binhex/arch-prowlarr | 0.0.0.0:9696->9696/tcp, :::9696->9696/tcp | Up 3 weeks (healthy) |
| pulse_neo4j | neo4j:2025.10.1-community-bullseye | 7473/tcp, 0.0.0.0:50210->7474/tcp, [::]:50210->7474/tcp, 0.0.0.0:50211->7687/tcp, [::]:50211->7687/tcp | Up 3 weeks (healthy) |
| qbittorrent | 70ea470ac756 | 0.0.0.0:6881->6881/tcp, :::6881->6881/tcp, 0.0.0.0:8080->8080/tcp, :::8080->8080/tcp, 6881/udp, 0.0.0.0:30153->30153/tcp, :::30153->30153/tcp | Up 3 weeks |
| radarr | d1aa08807c7e | 0.0.0.0:7878->7878/tcp, :::7878->7878/tcp | Up 12 days |
| redis | redis:alpine | 6379/tcp, 0.0.0.0:6379->80/tcp, [::]:6379->80/tcp | Up 2 weeks |
| sabnzbd | c02f7bbb0377 | 0.0.0.0:8095->8080/tcp, [::]:8095->8080/tcp | Up 12 days |
| scrutiny | 580c421f4c94 | 8080/tcp, 0.0.0.0:8081->80/tcp, [::]:8081->80/tcp | Up 3 weeks |
| shelfmark | ghcr.io/calibrain/shelfmark:latest | 0.0.0.0:8084->8084/tcp, :::8084->8084/tcp | Up 9 days (healthy) |
| sonarr | b09b31c97c92 | 0.0.0.0:8989->8989/tcp, :::8989->8989/tcp | Up 12 days |
| tautulli | dca7f28de78a | 0.0.0.0:8181->8181/tcp, :::8181->8181/tcp | Up 12 days |
| tracearr | ghcr.io/connorgallopo/tracearr:latest | 0.0.0.0:34000->3000/tcp, [::]:34000->3000/tcp | Up 3 days (healthy) |
| tracearr-db | timescale/timescaledb-ha:pg18.1-ts2.25.0 | 5432/tcp, 8008/tcp, 8081/tcp | Up 3 weeks (healthy) |
| tracearr-redis | 5068a1b35387 | 6379/tcp | Up 2 weeks (healthy) |
| vnstat | vergoh/vnstat:latest | 0.0.0.0:8685->8685/tcp, :::8685->8685/tcp | Up 2 weeks |
| wrapperr | aunefyren/wrapperr:latest | 0.0.0.0:8282->8282/tcp, :::8282->8282/tcp | Up 3 weeks |
| zipline | ghcr.io/diced/zipline:latest | 0.0.0.0:8092->3000/tcp, [::]:8092->3000/tcp | Up 2 days |
| zipline_postgres | postgres:16 | 0.0.0.0:8093->5432/tcp, [::]:8093->5432/tcp | Up 2 days (healthy) |
### dookie
| Container | Image | Ports | Status |
|---|---|---|---|
| agent-os-win11 | dockurr/windows | 0.0.0.0:8006->8006/tcp, [::]:8006->8006/tcp, 0.0.0.0:2222->22/tcp, [::]:2222->22/tcp, 0.0.0.0:33890->3389/tcp, 0.0.0.0:33890->3389/udp, [::]:33890->3389/tcp, [::]:33890->3389/udp | Up 2 days |
| agentmemory-iii-engine-1 | iiidev/iii:0.11.2 | 127.0.0.1:3111-3112->3111-3112/tcp, 127.0.0.1:9464->9464/tcp, 127.0.0.1:49134->49134/tcp | Up 2 days |
| apprise-mcp | apprise-mcp:dev | 0.0.0.0:40050->40050/tcp, [::]:40050->40050/tcp | Up 2 days (healthy) |
| arcane-agent | ghcr.io/getarcaneapp/arcane-headless:latest | 0.0.0.0:3553->3553/tcp, [::]:3553->3553/tcp | Up 2 days |
| arcane-mcp | arcane-mcp-arcane-mcp | 3000/tcp, 0.0.0.0:44332->44332/tcp, [::]:44332->44332/tcp | Up 2 days (healthy) |
| aurora-design-system | aurora-design-system:local | 0.0.0.0:50000->3000/tcp, [::]:50000->3000/tcp | Up 2 days |
| axon | axon:dev-runtime | 0.0.0.0:8001->8001/tcp | Up 18 hours (healthy) |
| axon-chrome | axon-axon-chrome | 0.0.0.0:6000->6000/tcp, [::]:6000->6000/tcp, 0.0.0.0:9222-9223->9222-9223/tcp, [::]:9222-9223->9222-9223/tcp | Up 29 hours (healthy) |
| axon-qdrant | qdrant/qdrant:v1.13.1 | 0.0.0.0:53333->6333/tcp, [::]:53333->6333/tcp, 0.0.0.0:53334->6334/tcp, [::]:53334->6334/tcp | Up 29 hours (healthy) |
| axon-tei | ghcr.io/huggingface/text-embeddings-inference:89-1.9 | 0.0.0.0:52000->80/tcp, [::]:52000->80/tcp | Up 29 hours (healthy) |
| dockersocket | ghcr.io/tecnativa/docker-socket-proxy:latest | 0.0.0.0:2375->2375/tcp, [::]:2375->2375/tcp | Up 2 days |
| example-mcp | rmcp-template:dev | 0.0.0.0:40060->40060/tcp, [::]:40060->40060/tcp | Up About an hour (healthy) |
| gotify-mcp | rustify:dev | 0.0.0.0:40020->40020/tcp, [::]:40020->40020/tcp | Up 2 days (healthy) |
| labby | labby:dev | 0.0.0.0:8765->8765/tcp, [::]:8765->8765/tcp | Up 10 hours |
| open-design | vanjayak/open-design:latest | 0.0.0.0:7456->7456/tcp, [::]:7456->7456/tcp | Up 2 days (healthy) |
| syslog-mcp | ghcr.io/jmagar/syslog-mcp:0.27.1 | 0.0.0.0:1514->1514/tcp, [::]:1514->1514/tcp, 0.0.0.0:3100->3100/tcp, 0.0.0.0:1514->1514/udp, [::]:3100->3100/tcp, [::]:1514->1514/udp | Up 30 hours (healthy) |
| tailscale-mcp | rustscale:dev | 0.0.0.0:40040->40040/tcp, [::]:40040->40040/tcp | Up 2 days (healthy) |
| unifi-mcp | rustifi:dev | 0.0.0.0:40030->40030/tcp, [::]:40030->40030/tcp | Up 2 days (healthy) |
| unraid-mcp | unrust:dev | 0.0.0.0:40010->40010/tcp, [::]:40010->40010/tcp | Up 2 days (healthy) |
### squirts
| Container | Image | Ports | Status |
|---|---|---|---|
| adguard | 11notes/adguard:0.107.64 | 0.0.0.0:53->53/tcp, [::]:53->53/tcp, 0.0.0.0:3000->3000/tcp, 0.0.0.0:53->53/udp, [::]:3000->3000/tcp, [::]:53->53/udp, 0.0.0.0:3010->80/tcp, [::]:3010->80/tcp | Up 2 days (healthy) |
| arcane-agent | ghcr.io/getarcaneapp/arcane-headless:latest | 0.0.0.0:3553->3553/tcp, [::]:3553->3553/tcp | Up 2 days |
| authelia | authelia/authelia | 0.0.0.0:9091->9091/tcp, [::]:9091->9091/tcp | Up 19 hours (healthy) |
| authelia-mariadb | lscr.io/linuxserver/mariadb | 0.0.0.0:3310->3306/tcp, [::]:3310->3306/tcp | Up 2 days |
| authelia-redis | bitnami/redis:latest | 0.0.0.0:6382->6379/tcp, [::]:6382->6379/tcp | Up 2 days |
| bytestash | ghcr.io/jordan-dalby/bytestash:latest | 0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp | Up 2 days |
| callback-relay | mcp-oauth-gateway-callback-relay | 8000/tcp | Up 2 days (healthy) |
| dockersocket | ghcr.io/tecnativa/docker-socket-proxy:latest | 0.0.0.0:2375->2375/tcp, [::]:2375->2375/tcp | Up 2 days |
| dockge | louislam/dockge | 0.0.0.0:5001->5001/tcp, [::]:5001->5001/tcp | Up 2 days (healthy) |
| dolt | dolthub/dolt-sql-server:latest | 7007/tcp, 33060/tcp, 0.0.0.0:3311->3306/tcp, [::]:3311->3306/tcp, 0.0.0.0:33110->8000/tcp, [::]:33110->8000/tcp | Up 2 days (healthy) |
| dozzle | amir20/dozzle:latest | 0.0.0.0:6947->8080/tcp, [::]:6947->8080/tcp | Up 2 days |
| gotify | gotify/server:latest | 0.0.0.0:8070->80/tcp, [::]:8070->80/tcp | Up 2 days (healthy) |
| karakeep | ghcr.io/karakeep-app/karakeep:release | 0.0.0.0:3031->3000/tcp, [::]:3031->3000/tcp | Up 2 days (healthy) |
| karakeep-chrome | gcr.io/zenika-hub/alpine-chrome:123 | - | Up 2 days |
| karakeep-meilisearch | getmeili/meilisearch:v1.11.1 | 7700/tcp | Up 2 days |
| linkding | sissbruecker/linkding | 0.0.0.0:9090->9090/tcp, [::]:9090->9090/tcp | Up 2 days (healthy) |
| maloja | krateng/maloja:latest | 0.0.0.0:42010->42010/tcp, [::]:42010->42010/tcp | Up 2 days |
| mcp-oauth | mcp-oauth-gateway-mcp-oauth | 8000/tcp | Up 2 days (healthy) |
| mcp-oauth-redis | 9210b8dc25f1 | 6379/tcp | Up 2 days (healthy) |
| memos | ghcr.io/usememos/memos | 0.0.0.0:5230->5230/tcp, [::]:5230->5230/tcp | Up 2 days |
| multi-scrobbler | f181896c0373 | 0.0.0.0:9078->9078/tcp, [::]:9078->9078/tcp | Up 2 days |
| onecli-postgres-1 | postgres:18-alpine | 127.0.0.1:5432->5432/tcp | Up 2 days (healthy) |
| opengist | ghcr.io/thomiceli/opengist | 0.0.0.0:2222->2222/tcp, [::]:2222->2222/tcp, 0.0.0.0:6157->6157/tcp, [::]:6157->6157/tcp, 6158/tcp | Up 2 days (healthy) |
| overseerr | 6fc38cdf52e7 | 0.0.0.0:5055->5055/tcp, [::]:5055->5055/tcp | Up 2 days |
| paperless | 5fc22275c864 | 0.0.0.0:8024->8000/tcp, [::]:8024->8000/tcp | Up 2 days (healthy) |
| paperless-cache | 63e868dc880e | 6379/tcp | Up 2 days |
| paperless-db | 019965b81888 | 5432/tcp | Up 2 days |
| portainer_agent | portainer/agent:2.32.0 | 0.0.0.0:9001->9001/tcp, [::]:9001->9001/tcp | Up 2 days |
| radicale | c18d2481cfd5 | 0.0.0.0:5232->5232/tcp, [::]:5232->5232/tcp | Up 2 days (healthy) |
| rustdesk-hbbr | rustdesk/rustdesk-server:latest | - | Up 2 days |
| rustdesk-hbbs | rustdesk/rustdesk-server:latest | - | Up 2 days |
| searxng | de25454e31a1 | 0.0.0.0:1236->8080/tcp, [::]:1236->8080/tcp | Up 2 days |
| searxng-redis | d10b936dd67d | 6379/tcp | Up 2 days |
| swag | lscr.io/linuxserver/swag | 0.0.0.0:80->80/tcp, [::]:80->80/tcp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp, 0.0.0.0:2002->22/tcp, [::]:2002->22/tcp | Up 18 hours |
| swag-mcp | ghcr.io/jmagar/swag-mcp:1.1.6 | 127.0.0.1:8012->8000/tcp | Up 2 days (healthy) |
| vaultwarden | vaultwarden/server | 0.0.0.0:4743->80/tcp, [::]:4743->80/tcp | Up 2 days (healthy) |
| wizarr | ghcr.io/wizarrrr/wizarr | 0.0.0.0:5690->5690/tcp, [::]:5690->5690/tcp | Up 2 days |
### shart
| Container | Image | Ports | Status |
|---|---|---|---|
| arcane-agent | ghcr.io/getarcaneapp/arcane-headless:latest | 0.0.0.0:3553->3553/tcp, :::3553->3553/tcp | Up 46 hours |
| dockersocket | ghcr.io/tecnativa/docker-socket-proxy:latest | 0.0.0.0:2375->2375/tcp, :::2375->2375/tcp | Up 46 hours |
| portainer_agent | portainer/agent:2.32.0 | 0.0.0.0:9001->9001/tcp, :::9001->9001/tcp | Up 46 hours |
### steamy / steamy-wsl
| Container | Image | Ports | Status |
|---|---|---|---|
| crawl4r-qdrant | qdrant/qdrant:gpu-nvidia-latest | 0.0.0.0:52001->6333/tcp, [::]:52001->6333/tcp, 0.0.0.0:52002->6334/tcp, [::]:52002->6334/tcp | Up 30 hours (healthy) |
### vivobook / vivobook-wsl
| Container | Image | Ports | Status |
|---|---|---|---|
| arcane-agent | ghcr.io/getarcaneapp/arcane-headless:latest | 0.0.0.0:3553->3553/tcp, [::]:3553->3553/tcp | Up 30 hours |

## Storage Architecture

### tootie - Unraid Array and Cache

```text
Filesystem      Size  Used Avail Use% Mounted on
shfs            199T  182T   17T  92% /mnt/user
cache           2.4T   54G  2.3T   3% /mnt/cache
```

Parity status excerpt:

```text
mdNumDisabled=2
diskName.0=
diskSize.0=0
rdevName.0=
```

Block devices excerpt:

```text
NAME      SIZE MODEL                        TYPE
loop0   651.8M                              loop
loop1   173.4M                              loop
loop2      10G                              loop
sda      10.9T WDC WD120EDBZ-11B1HA0        disk
sdb      10.9T WDC WD120EDBZ-11B1HA0        disk
sdc      12.7T WDC WD140EDGZ-11B1PA0        disk
sdd      16.4T WDC WD180EDGZ-11BLDS0        disk
sde      16.4T WDC WD180EDGZ-11BLDS0        disk
sdf      28.7G Cruzer Glide                 disk
sdg      16.4T WDC WD180EDGZ-11B2DA0        disk
sdh      16.4T WDC WD180EDGZ-11B2DA0        disk
sdi      16.4T WDC WD180EDGZ-11B2DA0        disk
sdj      16.4T WDC WD180EDGZ-11B2DA0        disk
sdk      16.4T WDC WD180EDGZ-11B2DA0        disk
sdl      16.4T WDC WD180EDGZ-11B2DA0        disk
sdm      16.4T WDC WD180EDGZ-11B2DA0        disk
sdn      16.4T WDC WD180EDGZ-11B2DA0        disk
md1p1    10.9T                              md
md2p1    10.9T                              md
md3p1    16.4T                              md
md4p1    12.7T                              md
md5p1    16.4T                              md
md6p1    16.4T                              md
md7p1    16.4T                              md
md8p1    16.4T                              md
md9p1    16.4T                              md
md10p1   16.4T                              md
md11p1   16.4T                              md
md12p1   16.4T                              md
md13p1   16.4T                              md
zram0       0B                              disk
nvme1n1   1.8T WD_BLACK SN7100 2TB          disk
nvme3n1   1.8T Samsung SSD 970 EVO Plus 2TB disk
nvme2n1   1.8T Samsung SSD 990 EVO Plus 2TB disk
```

### ZFS Pools

#### tootie

| Pool | Size | Allocated | Free | Frag | Health |
|---|---|---|---|---|---|
| cache | 5.45T | 1.85T | 3.61T | 28% | ONLINE |

#### squirts

| Pool | Size | Allocated | Free | Frag | Health |
|---|---|---|---|---|---|
| bpool | 1.88G | 1.25G | 636M | 53% | ONLINE |
| rpool | 920G | 178G | 742G | 46% | ONLINE |

#### shart

| Pool | Size | Allocated | Free | Frag | Health |
|---|---|---|---|---|---|
| backup | 7.27T | 1.80T | 5.47T | 20% | ONLINE |

## Reverse Proxy & Public Services

SWAG is expected on `squirts`. Active proxy config count is generated from `/mnt/appdata/swag/nginx/proxy-confs`.

| Metric | Value |
|---|---|
| Active config files | 149 |
| First 80 config-derived service names | `adguard-unbound`, `adminer`, `affine`, `agent-os`, `agents`, `agor`, `agregarr`, `api`, `apprise`, `arcane`, `audiobookshelf`, `aurora-design`, `auth-dinglebear`, `authelia`, `axon`, `bazarr`, `better-chatbot`, `big-agi`, `bolt`, `bookstack`, `bytestash`, `callback`, `changedetection`, `chrome-devtools`, `claude`, `clawdbot`, `cli-api`, `code-server-wildcard`, `code-server`, `comfyui`, `composecraft`, `context-forge`, `crontab-ui`, `dashboard`, `dcm`, `diskspeed`, `dockge`, `dockpeek`, `dozzle`, `esphome`, `fc-bridge`, `feishin`, `firecrawl`, `firefox`, `freshrss`, `ghbd`, `glances`, `gocron`, `gomft`, `gotify`, `homeassistant`, `homebox`, `homelab`, `immich`, `infisical`, `it-tools`, `jellyfin`, `joplin`, `karakeep`, `kavita`, `lab`, `linkding`, `maloja`, `mcp-auth`, `mcp`, `mcpx`, `mem0`, `memos`, `mesh`, `minio-s3-api`, `minio-web`, `multi-scrobbler`, `navidrome`, `neo4j-memory`, `neo4j`, `ngent`, `nonexistent.conf`, `notifiarr`, `nugget`, `obsidian-api` |

## AI / RAG / Agent Stack

### Axon on dookie

| Container | Image | Ports | Status |
|---|---|---|---|
| agentmemory-iii-engine-1 | iiidev/iii:0.11.2 | 127.0.0.1:3111-3112->3111-3112/tcp, 127.0.0.1:9464->9464/tcp, 127.0.0.1:49134->49134/tcp | Up 2 days |
| axon | axon:dev-runtime | 0.0.0.0:8001->8001/tcp | Up 18 hours (healthy) |
| axon-chrome | axon-axon-chrome | 0.0.0.0:6000->6000/tcp, [::]:6000->6000/tcp, 0.0.0.0:9222-9223->9222-9223/tcp, [::]:9222-9223->9222-9223/tcp | Up 29 hours (healthy) |
| axon-qdrant | qdrant/qdrant:v1.13.1 | 0.0.0.0:53333->6333/tcp, [::]:53333->6333/tcp, 0.0.0.0:53334->6334/tcp, [::]:53334->6334/tcp | Up 29 hours (healthy) |
| axon-tei | ghcr.io/huggingface/text-embeddings-inference:89-1.9 | 0.0.0.0:52000->80/tcp, [::]:52000->80/tcp | Up 29 hours (healthy) |
| labby | labby:dev | 0.0.0.0:8765->8765/tcp, [::]:8765->8765/tcp | Up 10 hours |

### GPU Inference on steamy

| Container | Image | Ports | Status |
|---|---|---|---|
| crawl4r-qdrant | qdrant/qdrant:gpu-nvidia-latest | 0.0.0.0:52001->6333/tcp, [::]:52001->6333/tcp, 0.0.0.0:52002->6334/tcp, [::]:52002->6334/tcp | Up 30 hours (healthy) |

## MCP Server Ecosystem

| MCP server | Host | Port | Observed image | Status |
|---|---|---|---|---|
| syslog-mcp | dookie | 1514 TCP/UDP, 3100 HTTP | ghcr.io/jmagar/syslog-mcp:0.27.1 | Up 30 hours (healthy) |
| arcane-mcp | dookie | 44332 | arcane-mcp-arcane-mcp | Up 2 days (healthy) |
| unraid-mcp | dookie | 40010 | unrust:dev | Up 2 days (healthy) |
| gotify-mcp | dookie | 40020 | rustify:dev | Up 2 days (healthy) |
| unifi-mcp | dookie | 40030 | rustifi:dev | Up 2 days (healthy) |
| tailscale-mcp | dookie | 40040 | rustscale:dev | Up 2 days (healthy) |
| apprise-mcp | dookie | 40050 | apprise-mcp:dev | Up 2 days (healthy) |
| example-mcp | dookie | 40060 | rmcp-template:dev | Up About an hour (healthy) |
| swag-mcp | squirts | 8012 localhost binding | ghcr.io/jmagar/swag-mcp:1.1.6 | Up 2 days (healthy) |

## Backup Strategy

- `shart` is the ZFS receive target.
- Backup job freshness is not inferred by this script. Check Sanoid/Syncoid logs or Gotify notifications before relying on current backup health.
- `shart` currently reports these ZFS pools:

| Pool | Size | Allocated | Free | Frag | Health |
|---|---|---|---|---|---|
| backup | 7.27T | 1.80T | 5.47T | 20% | ONLINE |

## Monitoring & Notifications

- `syslog-mcp` is expected on dookie at ports 1514 and 3100.
- Gotify is expected on squirts.
- This generator does not query application APIs or notification contents; it records container and host state only.

## Virtual Machines

- `dookie` is treated as the active Linux KVM guest hosted on tootie.
- VM inventory is not inferred by this script yet. Add `virsh list --all` collection on tootie if VM state needs to be authoritative here.

## Security Posture

- Public entrypoint: SWAG on squirts.
- Inter-node access: Tailscale and LAN SSH aliases.
- Vulnerability scan data is not generated here. Run Arcane/Trivy before acting on CVE status.
- tootie parity status is collected above; an empty parity slot remains a critical risk when observed.

## Known Issues & Follow-Up Checks

- If tootie parity excerpt shows `diskName.0=` or `diskSize.0=0`, parity is not assigned.
- If Arcane marks a host offline but SSH works, reconcile Arcane environment registration.
- If an expected service appears under "not observed", check whether it moved, stopped, or changed container name.
- Confirm backup freshness from Sanoid/Syncoid logs; this report does not prove backup success.

## Appendix: Key URLs

| Service | URL |
|---|---|
| Unraid Web UI | http://10.1.0.2:6969 |
| Syslog MCP | http://dookie:3100 |
| Arcane UI | https://arcane.tootie.tv |
| Arcane MCP | http://dookie:44332 |
| Unraid MCP | http://dookie:40010 |
| Plex | http://10.1.0.2:32400 |
| Windows sandbox noVNC | http://dookie:8006 |
| Windows sandbox RDP | dookie:33890 |
