---
description: Sync local skill symlinks and Claude agent symlinks
argument-hint: [--check|--dry-run|--sync] [--skills-only|--agents-only] [--verbose] [--strict-extras]
allowed-tools: Bash, Read
---

Current skill symlink status:

!`python3 /home/jmagar/.agents/scripts/sync-skills.py --check --format markdown || true`

Run the skill symlink sync helper using `$ARGUMENTS`.

If `$ARGUMENTS` is empty, run:

```bash
python3 /home/jmagar/.agents/scripts/sync-skills.py --sync --format markdown
```

Otherwise, run the helper with Markdown output and append the supplied arguments:

```bash
python3 /home/jmagar/.agents/scripts/sync-skills.py --format markdown $ARGUMENTS
```

Report:

- Whether Claude, Codex, Gemini, and Copilot skill directories are now synced to `~/.agents/src/skills`.
- Whether Claude's agent directory is now synced to `~/.agents/src/agents`.
- Any missing or stale symlinks that were created or updated.
- Any conflicts that were not changed because a canonical skill name is occupied by a non-symlink path.
- Any broken extra symlinks that still need manual review. These are warnings unless `--strict-extras` is passed.

Do not remove platform-specific extra skills or agents. This command only creates missing canonical links and updates stale canonical links whose names match directories under `~/.agents/src/skills` or Markdown files under `~/.agents/src/agents`. Codex agent syncing is intentionally out of scope for now.
