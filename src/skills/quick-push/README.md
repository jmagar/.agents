# quick-push

Stage all changes, optionally bump the project version, update CHANGELOG, commit with a Claude co-authorship trailer, push to the current (or a new feature) branch, then save a session log.

## What it does

1. **Orient** — read injected git state (branch, dirty files, recent commits).
2. **Bump** version if changes warrant it (skip with `--no-bump`). Updates `Cargo.toml`, `package.json`s, `pyproject.toml`, plugin manifests, README badges, etc., in sync.
3. **Changelog** — document prior commits under the new version heading; this push's own entry is amended in after the commit lands.
4. **Stage / commit / push** with a meaningful message and Claude trailer.
5. **Save session** via `save-to-md` (skipped silently if unavailable).

Never force-pushes. Halts on hook failures rather than skipping them.

## Invoke

Triggers: "quick push", "push my changes", "commit and push", "ship this", "push to a new branch". Slash-command oriented (`disable-model-invocation: true`).

## Arguments

- `--no-bump` — skip the version bump step

## Files

- `SKILL.md` — the workflow
