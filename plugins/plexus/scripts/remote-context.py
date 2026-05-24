#!/usr/bin/env python3
"""Build an agent-ready context block for a Plexus remote host."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REMOTES_DIR = PLUGIN_ROOT / "remotes"


@dataclass
class CommandResult:
    command: list[str]
    ok: bool
    stdout: str
    stderr: str


def run(command: list[str], timeout: int) -> CommandResult:
    try:
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return CommandResult(command, False, "", str(exc))

    return CommandResult(
        command=command,
        ok=proc.returncode == 0,
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
    )


def ssh(host: str, remote_command: str, timeout: int) -> CommandResult:
    return run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            f"ConnectTimeout={timeout}",
            host,
            remote_command,
        ],
        timeout=timeout + 2,
    )


def read_remote_md(host: str) -> tuple[Path, str]:
    path = REMOTES_DIR / host / "REMOTE.md"
    if not path.exists():
        raise SystemExit(f"No REMOTE.md profile found at {path}")
    return path, path.read_text(encoding="utf-8")


def probe_ssh(host: str, timeout: int) -> dict[str, Any]:
    probes = {
        "identity": "hostname; uname -a; printf 'user='; whoami",
        "uptime": "uptime",
        "resources": "free -h 2>/dev/null || true; df -h -x tmpfs -x devtmpfs 2>/dev/null | head -40 || true",
        "network": "hostname -I 2>/dev/null || true; ip route get 1.1.1.1 2>/dev/null || true",
        "systemd_failed": "systemctl --failed --no-pager 2>/dev/null || true",
        "docker": "if command -v docker >/dev/null 2>&1; then docker ps --format 'table {{.Names}}\\t{{.Image}}\\t{{.Status}}\\t{{.Ports}}'; else echo 'docker not found'; fi",
        "listeners": "if command -v ss >/dev/null 2>&1; then ss -tulpen 2>/dev/null | head -80; else echo 'ss not found'; fi",
    }
    return {name: vars(ssh(host, command, timeout)) for name, command in probes.items()}


def probe_tailscale(host: str, timeout: int) -> dict[str, Any] | None:
    if not shutil.which("tailscale"):
        return None
    result = run(["tailscale", "status", "--json"], timeout=timeout)
    if not result.ok or not result.stdout:
        return vars(result)
    try:
        status = json.loads(result.stdout)
    except json.JSONDecodeError:
        return vars(result)

    peers = status.get("Peer", {})
    matches = []
    for peer in peers.values():
        dns_name = peer.get("DNSName", "").rstrip(".")
        host_name = peer.get("HostName", "")
        if host in {dns_name, host_name} or dns_name.startswith(f"{host}."):
            matches.append(peer)
    return {"matches": matches, "count": len(matches)}


def probe_syslog(host: str, timeout: int) -> dict[str, Any] | None:
    if not shutil.which("syslog"):
        return None
    commands = {
        "tail": ["syslog", "tail", "-n", "20", "--hostname", host, "--json"],
        "errors": ["syslog", "errors", "--from", "24h", "--json"],
        "sessions": ["syslog", "sessions", "--hostname", host, "--limit", "10", "--json"],
    }
    return {name: vars(run(command, timeout=timeout)) for name, command in commands.items()}


def build_context(host: str, probe: bool, timeout: int) -> dict[str, Any]:
    remote_path, remote_md = read_remote_md(host)
    context: dict[str, Any] = {
        "host": host,
        "profile_path": str(remote_path),
        "remote_md": remote_md,
        "live": {},
    }
    if probe:
        context["live"]["ssh"] = probe_ssh(host, timeout)
        context["live"]["tailscale"] = probe_tailscale(host, timeout)
        context["live"]["syslog"] = probe_syslog(host, timeout)
    return context


def render_command_result(result: dict[str, Any]) -> str:
    status = "ok" if result.get("ok") else "failed"
    stdout = result.get("stdout") or ""
    stderr = result.get("stderr") or ""
    body = stdout if stdout else stderr
    if not body:
        body = "(no output)"
    return f"_status: {status}_\n\n```text\n{body}\n```"


def render_markdown(context: dict[str, Any]) -> str:
    lines = [
        f"# Plexus Remote Context: {context['host']}",
        "",
        f"Profile: `{context['profile_path']}`",
        "",
        "## Durable REMOTE.md Memory",
        "",
        context["remote_md"].rstrip(),
        "",
    ]

    live = context.get("live") or {}
    if not live:
        lines.extend(["## Live Context", "", "Live probes were skipped."])
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(["## Live SSH Context", ""])
    for name, result in (live.get("ssh") or {}).items():
        lines.extend([f"### {name}", "", render_command_result(result), ""])

    tailscale = live.get("tailscale")
    if tailscale is not None:
        lines.extend(["## Tailscale", "", "```json", json.dumps(tailscale, indent=2), "```", ""])

    syslog = live.get("syslog")
    if syslog is not None:
        lines.extend(["## syslog-mcp", ""])
        for name, result in syslog.items():
            lines.extend([f"### {name}", "", render_command_result(result), ""])

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="Remote host profile name under remotes/<host>/REMOTE.md")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--json", action="store_true", help="Alias for --format json")
    parser.add_argument("--no-probe", action="store_true", help="Read REMOTE.md without SSH/Tailscale/syslog probes")
    parser.add_argument("--timeout", type=int, default=6, help="Per-command timeout in seconds")
    args = parser.parse_args()

    output_format = "json" if args.json else args.format
    context = build_context(args.host, probe=not args.no_probe, timeout=args.timeout)
    if output_format == "json":
        print(json.dumps(context, indent=2))
    else:
        print(render_markdown(context), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
