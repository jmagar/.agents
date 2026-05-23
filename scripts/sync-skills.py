#!/usr/bin/env python3
"""Check and repair skill and agent symlinks across local runtimes."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_SOURCE = Path.home() / ".agents" / "src" / "skills"
DEFAULT_AGENT_SOURCE = Path.home() / ".agents" / "src" / "agents"
DEFAULT_TARGETS = {
    "claude": Path.home() / ".claude" / "skills",
    "codex": Path.home() / ".codex" / "skills",
    "gemini": Path.home() / ".gemini" / "skills",
    "copilot": Path.home() / ".copilot" / "skills",
}
DEFAULT_AGENT_TARGETS = {
    "claude-agents": Path.home() / ".claude" / "agents",
}


@dataclass
class TargetReport:
    name: str
    path: Path
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    ok: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    extras: list[str] = field(default_factory=list)
    broken_extras: list[str] = field(default_factory=list)
    missing_dir: bool = False

    @property
    def changed_count(self) -> int:
        return len(self.created) + len(self.updated)

    @property
    def problem_count(self) -> int:
        return len(self.conflicts) + len(self.broken_extras)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync ~/.agents/src/skills links and Claude agent links into local runtime dirs.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Report drift without changing files.")
    mode.add_argument("--sync", action="store_true", help="Create or update stale symlinks.")
    mode.add_argument("--dry-run", action="store_true", help="Show what --sync would change.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Canonical skill source directory.")
    parser.add_argument(
        "--agent-source",
        type=Path,
        default=DEFAULT_AGENT_SOURCE,
        help="Canonical agent source directory.",
    )
    parser.add_argument(
        "--target",
        action="append",
        metavar="NAME=PATH",
        help="Target skill directory. May be repeated. Defaults to claude/codex/gemini/copilot.",
    )
    parser.add_argument(
        "--agent-target",
        action="append",
        metavar="NAME=PATH",
        help="Target agent directory. May be repeated. Defaults to claude-agents=~/.claude/agents.",
    )
    parser.add_argument(
        "--skills-only",
        action="store_true",
        help="Only sync skill symlinks.",
    )
    parser.add_argument(
        "--agents-only",
        action="store_true",
        help="Only sync Claude agent symlinks.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "markdown"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--strict-extras",
        action="store_true",
        help="Return non-zero when broken non-canonical extra symlinks are found.",
    )
    parser.add_argument("--verbose", action="store_true", help="List all in-sync symlinks.")
    return parser.parse_args()


def parse_targets(values: list[str] | None) -> dict[str, Path]:
    if not values:
        return DEFAULT_TARGETS.copy()

    targets: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"--target must be NAME=PATH: {value}")
        name, path = value.split("=", 1)
        name = name.strip()
        if not name:
            raise SystemExit(f"--target name cannot be empty: {value}")
        targets[name] = Path(path).expanduser()
    return targets


def source_skills(source: Path) -> dict[str, Path]:
    if not source.is_dir():
        raise SystemExit(f"source skill directory does not exist: {source}")
    skills = {
        path.name: path.resolve()
        for path in source.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }
    if not skills:
        raise SystemExit(f"no source skills with SKILL.md found under: {source}")
    return dict(sorted(skills.items()))


def source_agent_files(source: Path) -> dict[str, Path]:
    if not source.is_dir():
        raise SystemExit(f"source agent directory does not exist: {source}")
    agents = {
        str(path.relative_to(source)): path.resolve()
        for path in source.rglob("*.md")
        if path.is_file()
    }
    if not agents:
        raise SystemExit(f"no source Claude agent markdown files found under: {source}")
    return dict(sorted(agents.items()))


def same_target(link: Path, expected: Path) -> bool:
    try:
        return link.resolve(strict=False) == expected.resolve(strict=False)
    except OSError:
        return False


def sync_target(
    name: str,
    target: Path,
    skills: dict[str, Path],
    *,
    sync: bool,
    dry_run: bool,
) -> TargetReport:
    report = TargetReport(name=name, path=target)
    if not target.exists():
        report.missing_dir = True
        if sync and not dry_run:
            target.mkdir(parents=True, exist_ok=True)
        elif not sync:
            report.conflicts.append("<target directory missing>")
            return report

    if not target.is_dir() and not dry_run:
        report.conflicts.append("<target path is not a directory>")
        return report

    for skill_name, source_path in skills.items():
        link = target / skill_name
        if link.is_symlink():
            if same_target(link, source_path):
                report.ok.append(skill_name)
            else:
                report.updated.append(skill_name)
                if sync and not dry_run:
                    link.unlink()
                    link.symlink_to(source_path, target_is_directory=True)
        elif link.exists():
            report.conflicts.append(skill_name)
        else:
            report.created.append(skill_name)
            if sync and not dry_run:
                link.symlink_to(source_path, target_is_directory=True)

    if target.exists() and target.is_dir():
        for child in sorted(target.iterdir(), key=lambda path: path.name):
            if child.name in skills:
                continue
            if child.is_symlink() and not child.exists():
                report.broken_extras.append(child.name)
            else:
                report.extras.append(child.name)

    return report


def sync_file_target(
    name: str,
    target: Path,
    entries: dict[str, Path],
    *,
    sync: bool,
    dry_run: bool,
) -> TargetReport:
    report = TargetReport(name=name, path=target)
    if not target.exists():
        report.missing_dir = True
        if sync and not dry_run:
            target.mkdir(parents=True, exist_ok=True)
        elif not sync:
            report.conflicts.append("<target directory missing>")
            return report

    if not target.is_dir() and not dry_run:
        report.conflicts.append("<target path is not a directory>")
        return report

    for rel_path, source_path in entries.items():
        link = target / rel_path
        if link.is_symlink():
            if same_target(link, source_path):
                report.ok.append(rel_path)
            else:
                report.updated.append(rel_path)
                if sync and not dry_run:
                    link.unlink()
                    link.parent.mkdir(parents=True, exist_ok=True)
                    link.symlink_to(source_path)
        elif link.exists():
            report.conflicts.append(rel_path)
        else:
            report.created.append(rel_path)
            if sync and not dry_run:
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(source_path)

    if target.exists() and target.is_dir():
        expected = set(entries)
        for child in sorted(target.rglob("*"), key=lambda path: str(path)):
            if child.is_dir():
                continue
            rel_path = str(child.relative_to(target))
            if rel_path in expected:
                continue
            if child.is_symlink() and not child.exists():
                report.broken_extras.append(rel_path)
            else:
                report.extras.append(rel_path)

    return report


def render_text(source: Path, reports: list[TargetReport], *, sync: bool, dry_run: bool, verbose: bool) -> str:
    action = "dry-run" if dry_run else "sync" if sync else "check"
    lines = [f"sync-skills {action}", f"source: {source}", ""]
    for report in reports:
        lines.append(f"{report.name}: {report.path}")
        if report.created:
            lines.append(f"  create: {', '.join(report.created)}")
        if report.updated:
            lines.append(f"  update: {', '.join(report.updated)}")
        if report.conflicts:
            lines.append(f"  conflicts: {', '.join(report.conflicts)}")
        if report.broken_extras:
            lines.append(f"  broken extras: {', '.join(report.broken_extras)}")
        if report.extras:
            lines.append(f"  extras left alone: {len(report.extras)}")
        if verbose and report.ok:
            lines.append(f"  ok: {', '.join(report.ok)}")
        if not any([report.created, report.updated, report.conflicts, report.broken_extras]) and not verbose:
            lines.append(f"  ok: {len(report.ok)} canonical symlinks")
        lines.append("")
    lines.append(summary_line(reports, sync=sync, dry_run=dry_run))
    return "\n".join(lines)


def render_markdown(source: Path, reports: list[TargetReport], *, sync: bool, dry_run: bool, verbose: bool) -> str:
    action = "dry-run" if dry_run else "sync" if sync else "check"
    lines = [f"### sync-skills {action}", "", f"- Source: `{source}`", ""]
    lines.append("| Target | OK | Create | Update | Conflicts | Broken extras | Extras left alone |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for report in reports:
        lines.append(
            f"| `{report.name}` | {len(report.ok)} | {len(report.created)} | {len(report.updated)} | "
            f"{len(report.conflicts)} | {len(report.broken_extras)} | {len(report.extras)} |"
        )
    lines.append("")
    for report in reports:
        details = []
        if report.created:
            details.append(f"create: {', '.join(report.created)}")
        if report.updated:
            details.append(f"update: {', '.join(report.updated)}")
        if report.conflicts:
            details.append(f"conflicts: {', '.join(report.conflicts)}")
        if report.broken_extras:
            details.append(f"broken extras: {', '.join(report.broken_extras)}")
        if verbose and report.ok:
            details.append(f"ok: {', '.join(report.ok)}")
        if details:
            lines.append(f"- `{report.name}`: " + "; ".join(details))
    lines.append("")
    lines.append(f"**Summary:** {summary_line(reports, sync=sync, dry_run=dry_run)}")
    return "\n".join(lines)


def summary_line(reports: list[TargetReport], *, sync: bool, dry_run: bool) -> str:
    created = sum(len(report.created) for report in reports)
    updated = sum(len(report.updated) for report in reports)
    conflicts = sum(len(report.conflicts) for report in reports)
    broken = sum(len(report.broken_extras) for report in reports)
    if sync and not dry_run:
        prefix = "applied"
    elif dry_run:
        prefix = "would apply"
    else:
        prefix = "drift"
    return f"{prefix}: create={created}, update={updated}, conflicts={conflicts}, broken_extras={broken}"


def main() -> int:
    args = parse_args()
    sync = args.sync
    dry_run = args.dry_run
    if not args.check and not args.sync and not args.dry_run:
        sync = True

    if args.skills_only and args.agents_only:
        raise SystemExit("--skills-only and --agents-only are mutually exclusive")

    reports: list[TargetReport] = []
    sources: list[Path] = []

    if not args.agents_only:
        source = args.source.expanduser().resolve(strict=False)
        sources.append(source)
        targets = parse_targets(args.target)
        skills = source_skills(source)
        reports.extend(
            sync_target(name, path.expanduser(), skills, sync=sync, dry_run=dry_run)
            for name, path in targets.items()
        )

    if not args.skills_only:
        agent_source = args.agent_source.expanduser().resolve(strict=False)
        sources.append(agent_source)
        agent_targets = parse_targets(args.agent_target) if args.agent_target else DEFAULT_AGENT_TARGETS.copy()
        agents = source_agent_files(agent_source)
        reports.extend(
            sync_file_target(name, path.expanduser(), agents, sync=sync, dry_run=dry_run)
            for name, path in agent_targets.items()
        )

    if args.format == "markdown":
        print(render_markdown(Path(", ".join(str(source) for source in sources)), reports, sync=sync, dry_run=dry_run, verbose=args.verbose))
    else:
        print(render_text(Path(", ".join(str(source) for source in sources)), reports, sync=sync, dry_run=dry_run, verbose=args.verbose))

    conflicts = sum(len(report.conflicts) for report in reports)
    broken = sum(len(report.broken_extras) for report in reports)
    if conflicts or (args.strict_extras and broken):
        return 2
    drift = sum(report.changed_count for report in reports)
    if not sync and drift:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
