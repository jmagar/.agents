#!/usr/bin/env python3
"""Generate the WillyNet homelab report from live host checks.

The script intentionally uses only stdlib Python plus non-interactive SSH so it
can run outside an agent session. It avoids secrets and records collection
failures inline instead of silently preserving stale values.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_TEMPLATE = REPO_ROOT / "src/skills/homelab-map/references/homelab.md"
DEFAULT_OUTPUT = Path.home() / ".homelab/homelab.md"


@dataclass(frozen=True)
class HostSpec:
    key: str
    label: str
    ssh_host: str
    role: str
    os_note: str
    ssh_port: int | None = None
    docker: bool = True
    zfs: bool = False
    unraid: bool = False


@dataclass
class CommandResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int | None = None


@dataclass
class HostSnapshot:
    spec: HostSpec
    hostname: str = ""
    kernel: str = ""
    uptime: str = ""
    memory: str = ""
    tailscale_ip: str = ""
    ipv4: list[str] = field(default_factory=list)
    containers: list[dict[str, str]] = field(default_factory=list)
    zpool: list[list[str]] = field(default_factory=list)
    df: list[str] = field(default_factory=list)
    extras: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


HOSTS = [
    HostSpec("tootie", "tootie", "tootie", "Primary NAS / app server", "Unraid", ssh_port=29229, zfs=True, unraid=True),
    HostSpec("dookie", "dookie", "dookie", "Dev / AI / MCP hub", "Linux KVM guest on tootie", zfs=False),
    HostSpec("squirts", "squirts", "squirts", "Edge services", "Ubuntu", zfs=True),
    HostSpec("shart", "shart", "shart", "ZFS backup target", "Unraid", zfs=True, unraid=True),
    HostSpec("steamy", "steamy / steamy-wsl", "steamy-wsl", "GPU workloads", "Windows 11 + WSL2"),
    HostSpec("vivobook", "vivobook / vivobook-wsl", "vivobook-wsl", "Mobile dev laptop", "Windows 11 + WSL2"),
]

SERVICE_HINTS = {
    "tootie": [
        "plex", "sonarr", "radarr", "bazarr", "prowlarr", "qbittorrent", "sabnzbd",
        "tautulli", "immich", "audiobookshelf", "kavita", "navidrome", "minio",
        "loggifly", "notifiarr", "apprise-api", "olivetin", "zipline",
    ],
    "dookie": [
        "axon", "axon-qdrant", "axon-tei", "axon-chrome", "syslog-mcp",
        "arcane-mcp", "unraid-mcp", "gotify-mcp", "unifi-mcp", "tailscale-mcp",
        "apprise-mcp", "labby", "agent-os-win11",
    ],
    "squirts": [
        "swag", "authelia", "adguard", "gotify", "vaultwarden", "paperless",
        "linkding", "karakeep", "bytestash", "memos", "radicale", "searxng",
        "dockge", "dozzle", "rustdesk", "multi-scrobbler", "maloja",
    ],
    "shart": ["arcane-agent", "portainer_agent", "dockersocket"],
    "steamy": ["crawl4r-qdrant", "arcane-agent"],
    "vivobook": ["arcane-agent"],
}

MCP_HINTS = [
    ("syslog-mcp", "dookie", "1514 TCP/UDP, 3100 HTTP"),
    ("arcane-mcp", "dookie", "44332"),
    ("unraid-mcp", "dookie", "40010"),
    ("gotify-mcp", "dookie", "40020"),
    ("unifi-mcp", "dookie", "40030"),
    ("tailscale-mcp", "dookie", "40040"),
    ("apprise-mcp", "dookie", "40050"),
    ("example-mcp", "dookie", "40060"),
    ("swag-mcp", "squirts", "8012 localhost binding"),
]


def run_local(argv: list[str], timeout: int = 20) -> CommandResult:
    try:
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=timeout, check=False)
        return CommandResult(proc.returncode == 0, proc.stdout.strip(), proc.stderr.strip(), proc.returncode)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return CommandResult(False, "", str(exc), None)


def ssh_command(spec: HostSpec, remote_command: str, timeout: int = 20) -> CommandResult:
    argv = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
    ]
    if spec.ssh_port:
        argv.extend(["-p", str(spec.ssh_port)])
    argv.extend([spec.ssh_host, remote_command])
    return run_local(argv, timeout=timeout)


def first_line(text: str) -> str:
    return text.splitlines()[0].strip() if text.strip() else ""


def parse_docker_json(lines: Iterable[str]) -> list[dict[str, str]]:
    containers: list[dict[str, str]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        containers.append({
            "name": item.get("Names", ""),
            "image": item.get("Image", ""),
            "ports": item.get("Ports", ""),
            "status": item.get("Status", ""),
        })
    return sorted(containers, key=lambda item: item["name"])


def collect_host(spec: HostSpec) -> HostSnapshot:
    snap = HostSnapshot(spec)

    basics = ssh_command(
        spec,
        "printf 'HOSTNAME='; hostname; "
        "printf 'KERNEL='; uname -sr; "
        "printf 'UPTIME='; uptime -p; "
        "printf 'MEMORY='; free -h | awk '/Mem:/ {print $3 \" / \" $2 \" used\"}'; "
        "printf 'TS='; tailscale ip -4 2>/dev/null || true; "
        "printf 'IPV4\\n'; ip -4 -brief addr 2>/dev/null || true",
    )
    if basics.ok:
        ipv4_mode = False
        for line in basics.stdout.splitlines():
            if line == "IPV4":
                ipv4_mode = True
                continue
            if ipv4_mode:
                if line.strip():
                    snap.ipv4.append(line.strip())
                continue
            if line.startswith("HOSTNAME="):
                snap.hostname = line.removeprefix("HOSTNAME=").strip()
            elif line.startswith("KERNEL="):
                snap.kernel = line.removeprefix("KERNEL=").strip()
            elif line.startswith("UPTIME="):
                snap.uptime = line.removeprefix("UPTIME=").strip()
            elif line.startswith("MEMORY="):
                snap.memory = line.removeprefix("MEMORY=").strip()
            elif line.startswith("TS="):
                snap.tailscale_ip = line.removeprefix("TS=").strip()
    else:
        snap.errors.append(f"basic SSH collection failed: {basics.stderr or basics.returncode}")

    if spec.docker:
        docker = ssh_command(spec, "docker ps --format '{{json .}}'", timeout=30)
        if docker.ok:
            snap.containers = parse_docker_json(docker.stdout.splitlines())
        else:
            snap.errors.append(f"docker ps failed: {docker.stderr or docker.returncode}")

    if spec.zfs:
        zpool = ssh_command(spec, "zpool list -H -o name,size,alloc,free,frag,health 2>/dev/null || true")
        if zpool.ok and zpool.stdout:
            snap.zpool = [line.split("\t") for line in zpool.stdout.splitlines() if line.strip()]

    if spec.unraid:
        df = ssh_command(spec, "df -h /mnt/user /mnt/cache 2>/dev/null || df -h /mnt/user 2>/dev/null || true")
        if df.ok and df.stdout:
            snap.df = df.stdout.splitlines()
        if spec.key == "tootie":
            parity = ssh_command(
                spec,
                "mdcmd status 2>/dev/null | egrep 'mdNumDisabled|diskName\\.0|rdevName\\.0|diskSize\\.0' || true",
            )
            snap.extras["parity"] = parity.stdout if parity.ok else ""
            lsblk = ssh_command(spec, "lsblk -d -o NAME,SIZE,MODEL,TYPE 2>/dev/null | sed -n '1,40p' || true")
            snap.extras["lsblk"] = lsblk.stdout if lsblk.ok else ""

    if spec.key == "squirts":
        swag = ssh_command(
            spec,
            "d=/mnt/appdata/swag/nginx/proxy-confs; "
            "if [ -d \"$d\" ]; then find \"$d\" -maxdepth 1 -type f -name '*.conf' -printf '%f\\n' | sort; fi",
            timeout=20,
        )
        if swag.ok:
            snap.extras["swag_configs"] = swag.stdout
        else:
            snap.errors.append(f"SWAG config listing failed: {swag.stderr or swag.returncode}")

    return snap


def lan_ip(snapshot: HostSnapshot) -> str:
    for line in snapshot.ipv4:
        for token in line.split():
            if token.startswith("10.1.0."):
                return token.split("/")[0]
    return ""


def container_count(snapshot: HostSnapshot) -> str:
    return str(len(snapshot.containers)) if snapshot.containers else "not collected"


def has_container(snapshot: HostSnapshot, name: str) -> bool:
    return any(c["name"] == name or name in c["name"] for c in snapshot.containers)


def find_container(snapshot: HostSnapshot, name: str) -> dict[str, str] | None:
    for container in snapshot.containers:
        if container["name"] == name or name in container["name"]:
            return container
    return None


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines.extend("| " + " | ".join(cell.replace("\n", "<br>") for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def bullet_list(items: Iterable[str]) -> str:
    values = [item for item in items if item]
    return "\n".join(f"- {item}" for item in values) if values else "- none observed"


def format_container_table(snapshot: HostSnapshot) -> str:
    rows = []
    for container in snapshot.containers:
        rows.append([container["name"], container["image"], container["ports"] or "-", container["status"] or "-"])
    return table(["Container", "Image", "Ports", "Status"], rows) if rows else "_No containers collected._"


def format_zpool(snapshot: HostSnapshot) -> str:
    rows = []
    for entry in snapshot.zpool:
        padded = entry + [""] * (6 - len(entry))
        rows.append(padded[:6])
    return table(["Pool", "Size", "Allocated", "Free", "Frag", "Health"], rows) if rows else "_No ZFS pool data collected._"


def service_host_rows(snapshots: dict[str, HostSnapshot]) -> list[list[str]]:
    rows = []
    for host, services in SERVICE_HINTS.items():
        snapshot = snapshots[host]
        observed = []
        missing = []
        for service in services:
            (observed if has_container(snapshot, service) else missing).append(service)
        rows.append([
            snapshot.spec.label,
            ", ".join(observed) if observed else "-",
            ", ".join(missing) if missing else "-",
        ])
    return rows


def render_report(snapshots: dict[str, HostSnapshot], generated_at: dt.datetime) -> str:
    swag_configs = snapshots["squirts"].extras.get("swag_configs", "")
    swag_names = [line for line in swag_configs.splitlines() if line.strip()]
    total_containers = sum(len(s.containers) for s in snapshots.values())
    tootie_df = "\n".join(snapshots["tootie"].df)
    tootie_parity = snapshots["tootie"].extras.get("parity", "").strip()

    node_rows = []
    for key in ["tootie", "dookie", "squirts", "shart", "steamy", "vivobook"]:
        snap = snapshots[key]
        node_rows.append([
            snap.spec.label,
            snap.spec.role,
            lan_ip(snap) or "not observed",
            snap.tailscale_ip or "not observed",
            snap.spec.os_note,
            snap.kernel or "not observed",
            snap.uptime or "not observed",
            snap.memory or "not observed",
            container_count(snap),
        ])

    mcp_rows = []
    for name, host, port in MCP_HINTS:
        snap = snapshots[host]
        container = find_container(snap, name)
        mcp_rows.append([
            name,
            snap.spec.label,
            port,
            container["image"] if container else "not observed",
            container["status"] if container else "not observed",
        ])

    public_examples = ", ".join(f"`{name.removesuffix('.subdomain.conf').removesuffix('.subfolder.conf')}`" for name in swag_names[:80])
    collection_errors = []
    for snap in snapshots.values():
        for error in snap.errors:
            collection_errors.append(f"{snap.spec.label}: {error}")

    return f"""# WillyNet Homelab - Infrastructure Documentation

> Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S %Z')}
> Generator: `src/skills/homelab-map/scripts/generate-homelab-report.py`
> Collection method: non-interactive SSH, Docker CLI, ZFS CLI, Unraid shell commands, and SWAG config files.

---

## Overview

{table(["Metric", "Value"], [
    ["Total nodes", str(len(snapshots))],
    ["Total containers running", str(total_containers)],
    ["Active SWAG proxy configs", str(len(swag_names)) if swag_names else "not collected"],
    ["Network", "WillyNet / 10.1.0.0/24 plus Tailscale mesh"],
    ["Primary public domain", "*.tootie.tv via SWAG on squirts"],
])}

## Collection Notes

{bullet_list(collection_errors) if collection_errors else "- All configured host collection commands completed successfully."}

Values in this document are a fresh runtime snapshot. Re-run the generator before making operational decisions:

```bash
python3 src/skills/homelab-map/scripts/generate-homelab-report.py
```

## Nodes

{table(["Name", "Role", "LAN IP", "Tailscale IP", "OS", "Kernel", "Uptime", "Memory", "Containers"], node_rows)}

### Network Interfaces

{chr(10).join(f"#### {snap.spec.label}{chr(10)}{bullet_list(f'`{line}`' for line in snap.ipv4)}" for snap in snapshots.values())}

## Service Location Summary

Observed means the expected container name was found in the live `docker ps` output for that host. Missing may mean the service moved, is stopped, has a different container name, or is only represented by a SWAG config.

{table(["Host", "Expected services observed", "Expected services not observed"], service_host_rows(snapshots))}

## Host Container Inventory

{chr(10).join(f"### {snap.spec.label}{chr(10)}{format_container_table(snap)}" for snap in snapshots.values())}

## Storage Architecture

### tootie - Unraid Array and Cache

```text
{tootie_df or 'not collected'}
```

Parity status excerpt:

```text
{tootie_parity or 'not collected'}
```

Block devices excerpt:

```text
{snapshots["tootie"].extras.get("lsblk", "not collected")}
```

### ZFS Pools

#### tootie

{format_zpool(snapshots["tootie"])}

#### squirts

{format_zpool(snapshots["squirts"])}

#### shart

{format_zpool(snapshots["shart"])}

## Reverse Proxy & Public Services

SWAG is expected on `squirts`. Active proxy config count is generated from `/mnt/appdata/swag/nginx/proxy-confs`.

{table(["Metric", "Value"], [
    ["Active config files", str(len(swag_names)) if swag_names else "not collected"],
    ["First 80 config-derived service names", public_examples or "not collected"],
])}

## AI / RAG / Agent Stack

### Axon on dookie

{format_container_table(HostSnapshot(
    spec=snapshots["dookie"].spec,
    containers=[c for c in snapshots["dookie"].containers if c["name"].startswith("axon") or c["name"] in {"labby", "agentmemory-iii-engine-1"}],
))}

### GPU Inference on steamy

{format_container_table(snapshots["steamy"])}

## MCP Server Ecosystem

{table(["MCP server", "Host", "Port", "Observed image", "Status"], mcp_rows)}

## Backup Strategy

- `shart` is the ZFS receive target.
- Backup job freshness is not inferred by this script. Check Sanoid/Syncoid logs or Gotify notifications before relying on current backup health.
- `shart` currently reports these ZFS pools:

{format_zpool(snapshots["shart"])}

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

{table(["Service", "URL"], [
    ["Unraid Web UI", "http://10.1.0.2:6969"],
    ["Syslog MCP", "http://dookie:3100"],
    ["Arcane UI", "https://arcane.tootie.tv"],
    ["Arcane MCP", "http://dookie:44332"],
    ["Unraid MCP", "http://dookie:40010"],
    ["Plex", "http://10.1.0.2:32400"],
    ["Windows sandbox noVNC", "http://dookie:8006"],
    ["Windows sandbox RDP", "dookie:33890"],
])}
"""


def render_with_template(report_body: str, template_path: Path) -> str:
    template = template_path.read_text()
    placeholder = "{{generated_report}}"
    if placeholder not in template:
        raise ValueError(f"template must contain {placeholder}")
    return template.replace(placeholder, report_body.rstrip() + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the WillyNet homelab markdown report.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"Output file. Default: {DEFAULT_OUTPUT}")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help=f"Template file. Default: {DEFAULT_TEMPLATE}")
    parser.add_argument("--stdout", action="store_true", help="Print report instead of writing it.")
    parser.add_argument("--no-write", action="store_true", help="Collect and render, but do not write the output file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshots = {spec.key: collect_host(spec) for spec in HOSTS}
    now = dt.datetime.now().astimezone()
    report_body = render_report(snapshots, now)
    report = render_with_template(report_body, args.template)

    if args.stdout:
        print(report)

    if not args.stdout and not args.no_write:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report)
        print(output)
    elif args.no_write:
        print("Rendered report without writing.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
