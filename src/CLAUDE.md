# Source Tree Guidance

This `src/` tree is the editable source for local agent components. Treat it as
hand-authored source, not generated output. When guidance in the repo root is
broader or older, this file is the local authority for work inside `src/`.

## Component Layout

- `skills/<name>/` is the canonical local skill source. The old root
  `skills/` path and older `shared/skills` references are stale for current
  work in this repo.
- `agents/<namespace>/<agent>.md` stores Claude-style Markdown agents.
  Preserve the namespace directory to avoid filename collisions such as repeated
  `code-reviewer.md` agents.
- `agents/codex/*.toml` stores Codex custom-agent definitions. Do not convert
  Claude Markdown agents to Codex TOML by assumption; use a separate explicit
  conversion/design pass.
- `commands/**/*.md` stores slash commands. Commands are instructions to the
  agent, not user-facing prose.
- `mcp/` stores MCP config fragments. Never commit live credentials.
- Empty component roots such as `hooks/`, `hook-scripts/`, `channels/`,
  `monitors/`, `output-styles/`, `prompts/`, `settings/`, `themes/`, `bin/`,
  and `lsp/` are reserved shape markers until they have real content.

## Skill Bundle Contract

Every skill directory should have these files:

- `SKILL.md`
- `README.md`
- `CHANGELOG.md`
- `agents/openai.yaml`

Optional support directories are `references/`, `scripts/`, `assets/`, and
`examples/`. Use them only when they directly support execution. Keep detailed
reference material out of `SKILL.md` and load it progressively from
`references/`.

`SKILL.md` frontmatter should stay minimal and useful:

- Required: `name`, `description`
- Optional command-style fields only when the skill is intentionally acting as a
  slash-command surface, for example `allowed-tools`, `argument-hint`, or
  `disable-model-invocation`
- Quote or fold YAML strings containing colons or other YAML-sensitive text

The `description` is the trigger surface. Make it concrete: include real user
phrases and the operational domain. Avoid generic descriptions that could
over-trigger.

`agents/openai.yaml` should include:

- `interface.display_name`
- `interface.short_description` between 25 and 64 characters
- `interface.default_prompt` containing the literal `$skill-name`

Preserve existing curated icon fields or policy/dependency sections when
normalizing OpenAI metadata.

## Common Skill Patterns

Lab service skills use this shape:

1. Prefer the MCP tool when it is available.
2. Discover live actions with `help` and action schemas before guessing.
3. Fall back to the matching CLI only when MCP is unavailable.
4. Keep large action catalogs in `references/mcp.md` and `references/cli.md`.
5. Document where credentials live, usually `~/.lab/.env`, without copying
   secrets.

Operational service skills without an MCP tool should still be actionable:

- Identify the target server, auth source, and scope before writes.
- Use API, CLI, container state, and logs as fallback surfaces.
- Treat deletes, permission changes, metadata rewrites, imports, rescans, and
  alert enabling as writes that need exact object names or ids.
- Prefer concrete fallback commands or API paths over scaffold text.

Do not leave `SKILL.md` files saying only "scaffolded" once the skill is part of
the live inventory. Either add a real workflow or narrow the description so it
does not promise missing behavior.

## Commands

Slash command files live under `commands/` and use Markdown frontmatter:

```yaml
---
description: Short action phrase for /help
argument-hint: [optional-args]
allowed-tools: Bash, Read
---
```

Use dynamic context injection for checks that should run at invocation time:

```markdown
Current status:

!`python3 /home/jmagar/.agents/scripts/sync-skills.py --check --format markdown || true`
```

Write command bodies as direct instructions to the agent. Do not write
marketing/explanation text to the user in place of executable instructions.

The `sync-skills` command is the current model for a command backed by a
reusable helper script:

- command: `commands/sync-skills.md`
- helper: `/home/jmagar/.agents/scripts/sync-skills.py`
- dynamic context: `--check --format markdown`
- default action: sync canonical links

## Agents

Claude agents are Markdown files with frontmatter and a prompt body:

```yaml
---
name: kotlin-specialist
description: "Use when ..."
model: inherit
tools: Read, Write, Edit, Bash, Glob, Grep
---
```

Codex agents are TOML files, not Claude Markdown/frontmatter. Keep fields such
as `model`, `model_reasoning_effort`, `sandbox_mode`, and
`developer_instructions` in TOML. If adding Codex coverage for an existing Claude
agent, create or work the Beads item for Codex-equivalent agent design rather
than guessing a lossy conversion.

For Claude agent sync, preserve the namespace tree:

```text
src/agents/plugin-dev/skill-reviewer.md
~/.claude/agents/plugin-dev/skill-reviewer.md -> ~/.agents/src/agents/plugin-dev/skill-reviewer.md
```

Do not flatten agent names into a single directory.

## Sync And Discovery

After adding, renaming, or removing skills or Claude agents, run:

```bash
python3 /home/jmagar/.agents/scripts/sync-skills.py --sync --format markdown
```

For a read-only check:

```bash
python3 /home/jmagar/.agents/scripts/sync-skills.py --check --format markdown
```

Current sync behavior:

- Skills sync from `~/.agents/src/skills` to `~/.claude/skills`,
  `~/.codex/skills`, `~/.gemini/skills`, and `~/.copilot/skills`.
- Claude agents sync from `~/.agents/src/agents/**/*.md` to
  `~/.claude/agents/<namespace>/<agent>.md`.
- Codex agent sync is intentionally not implemented yet.
- Platform-specific extras are left alone. Broken extras are warnings unless
  `--strict-extras` is passed.

The helper only updates canonical links whose names/paths match source entries.
It must not delete platform-specific extras.

## Validation

Use focused checks before committing:

```bash
git diff --check -- src
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/sync-skills.py
python3 /home/jmagar/.agents/scripts/sync-skills.py --check --format text
```

For skill metadata coverage:

```bash
python3 - <<'PY'
from pathlib import Path
import re, yaml

for skill in sorted(Path("src/skills").iterdir()):
    if not skill.is_dir():
        continue
    for rel in ("SKILL.md", "README.md", "CHANGELOG.md", "agents/openai.yaml"):
        if not (skill / rel).exists():
            raise SystemExit(f"missing {skill.name}/{rel}")
    meta = yaml.safe_load(re.match(r"^---\n(.*?)\n---\n", (skill / "SKILL.md").read_text(), re.S).group(1)) or {}
    openai = yaml.safe_load((skill / "agents/openai.yaml").read_text()) or {}
    prompt = (openai.get("interface") or {}).get("default_prompt", "")
    if f"${meta['name']}" not in prompt:
        raise SystemExit(f"bad default_prompt: {skill}/agents/openai.yaml")
print("skills ok")
PY
```

Avoid `python3 -m py_compile` without `PYTHONDONTWRITEBYTECODE=1`, or clean up
`__pycache__/` before staging.

## Git Hygiene

- This repo commonly has concurrent untracked skill work. Check
  `git status --short --untracked-files=all` before broad staging.
- Do not use `git add .` unless the user explicitly asks for it.
- Do not revert unrelated dirty files in sibling skill directories.
- If the user asks to commit and push, run `git pull --rebase`, `bd dolt push`,
  `git push`, and verify `HEAD...origin/main` is `0 0`.
