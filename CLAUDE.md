# `~/.agents/` — Jacob's agent marketplace workshop

This directory is Jacob's local agent-component workshop and multi-marketplace source repo. It contains the personal skill kit plus source/generated structure for Claude Code and Codex plugin bundles.

Local skills live under `src/skills/`. The previous root `skills/` directory has been migrated and is no longer a canonical source location.

The existing root `plugins/` directory is legacy/scratch space unless explicitly repurposed later. It is not part of the new marketplace bucket layout.

## Layout

```
~/.agents/
├── CLAUDE.md              ← you are here
├── .claude-plugin/        ← Claude marketplace root
│   └── marketplace.json  ← single Claude manifest
├── .agents/               ← Codex marketplace root
│   └── plugins/
│       └── marketplace.json  ← single Codex manifest
├── plugins/               ← all local plugin payloads (not curated)
│   └── <plugin-name>/
│       └── agents/
│           ├── claude/
│           │   └── <agent-name>.md    ← Claude agent (markdown + frontmatter)
│           └── codex/
│               └── <agent-name>.toml ← Codex agent (TOML)
├── src/                   ← handwritten shared components (never generated)
│   ├── skills/            ← local skill inventory, one dir per skill
│   ├── agents/            ← shared agent source / prompt bodies
│   ├── commands/
│   ├── hooks/
│   └── mcp/
├── catalog/               ← plugin registry + fork tracking metadata
│   └── plugins/           ← one YAML per plugin
├── templates/             ← plugin skeleton reference
├── scripts/               ← repo maintenance scripts
│   ├── fork-diff.sh       ← diff a forked plugin against its upstream
│   └── fork-list.sh       ← list all plugins with fork metadata
└── docs/                  ← specs, contracts, session logs
    └── sessions/
```

**Every skill MUST have:** `SKILL.md`, `README.md`, `CHANGELOG.md`. Scripts and references are optional.

## Marketplace architecture

This repo is a single marketplace with two manifests — one per platform:

- Claude Code: `.claude-plugin/marketplace.json`
- Codex: `.agents/plugins/marketplace.json`

Plugin source types in the manifest:
- **Upstream** (`git-subdir`, `url`, `github`): no local payload needed. Curated/untouched external plugins.
- **Local** (`./plugins/<name>`): payload lives in `plugins/<plugin-name>/`. Used for original, homelab-specific, or forked plugins.

### Forked plugins

A forked plugin is one that started as an upstream plugin but has local modifications. Forks are **not** a separate marketplace bucket — they live in whichever bucket matches their intent (a patched homelab service plugin → `flow-marketplace/`, an extended vibe project → `vibe-marketplace/`). The fork relationship is tracked in `catalog/plugins/<name>.yaml`.

**Catalog YAML schema for forks:**

```yaml
name: my-forked-plugin
bucket: flow-marketplace          # which bucket holds the local payload
upstream:
  source: git-subdir              # original source type (git-subdir | url | github)
  url: https://github.com/org/repo.git
  path: plugins/plugin-name       # omit if the whole repo is the plugin
  sha: abc123def456               # upstream commit SHA at time of fork
fork:
  forked_on: "2026-05-18"
  reason: "Added homelab proxy headers, disabled telemetry"
```

**Invariants:**
- A plugin in `curated-marketplace` MUST NOT have a `fork:` key — curated means untouched upstream. Move it to the appropriate bucket before adding local modifications.
- `upstream.sha` is the pinned commit at fork time. Update it when you intentionally rebase onto a newer upstream.

**Scripts:**

```bash
# Show diff between local payload and upstream at tracked SHA
scripts/fork-diff.sh <plugin-name>

# List all plugins with fork metadata
scripts/fork-list.sh
```

## Component placement

Use shared source directories for canonical component intent and per-platform directories for emitted package formats.

`shared/` contains the reusable content itself: skill directories, prompts, hook scripts, MCP fragments, command bodies, themes, and other files humans edit as the capability source.

`catalog/` contains package metadata about that content: plugin membership, target platforms, marketplace bucket, provenance, generation rules, publishability, source-to-output mappings, and fork tracking (upstream URL, pinned SHA, reason for divergence). Do not duplicate the full capability body in catalog files.

Rule of thumb:

- Edit the capability itself in `shared/`.
- Edit plugin inventory, ownership, targets, provenance, package membership, or generator behavior in `catalog/plugins/<plugin-id>.yaml`.

| Component | Shared/source location | Per-plugin/platform location |
|---|---|---|
| Agents | `shared/agents/`, `shared/prompts/` | `plugins/<name>/agents/{claude,codex}/` |
| Commands | `shared/commands/` | `plugins/<name>/commands/claude/` |
| Hooks | `shared/hooks/`, `shared/hook-scripts/` | `plugins/<name>/hooks/{claude,codex}/` |
| Skills | `src/skills/` | `plugins/<name>/skills/` |
| Output styles | `shared/output-styles/` | `plugins/<name>/output-styles/` |
| Channels | `shared/channels/` | `plugins/<name>/channels/` |
| Monitors | `shared/monitors/` | `plugins/<name>/monitors/` |
| Themes | `shared/themes/` | `plugins/<name>/themes/` |
| MCP servers | `shared/mcp/` | `plugins/<name>/mcp/` |
| LSP servers | `shared/lsp/` | `plugins/<name>/lsp/` |
| `bin/` tools | `shared/bin/` for reusable tools | `plugins/<name>/bin/` |
| Plugin settings | `shared/settings/` | `plugins/<name>/settings/` or plugin root `settings.json` |

Agents are intentionally platform-specific at packaging time. Claude agents are Markdown/frontmatter, and Codex agents are standalone TOML and may need separate installation. Keep the common prompt/intent in `shared/agents/`, then use `catalog/plugins/<plugin-id>.yaml` to decide which plugin includes it and which platform outputs are generated.

Codex plugin support is not identical to Claude plugin support. In particular, do not assume Codex can distribute every component Claude can. Keep Codex-only installation steps explicit when a component must be written into user or project config outside the plugin payload.

## Plugin skeletons

The full plugin skeleton lives in `templates/plugin/` and is mirrored as `_template/` under each marketplace bucket. It includes:

```
.claude-plugin/
.codex-plugin/
agents/{claude,codex}/
commands/claude/
hooks/{claude,codex}/
skills/
output-styles/
channels/
monitors/
themes/
mcp/
lsp/
bin/
settings/
```

Use `_template/` as a shape reference only. Do not put real plugin content there unless the intent is to change the template for future plugins.

## Skill discovery — the symlink farm

Claude Code discovers skills from `~/.claude/skills/<name>/SKILL.md`. The skills in *this* repo live at `~/.agents/src/skills/<name>/`, and are exposed to Claude via **symlinks** in `~/.claude/skills/`:

```bash
ls -la ~/.claude/skills/ | grep agents
# lrwxrwxrwx ... screenshots -> /home/jmagar/.agents/src/skills/screenshots
# lrwxrwxrwx ... chrome      -> /home/jmagar/.agents/src/skills/chrome
# ...
```

**Implication:** writing a SKILL.md under `~/.agents/src/skills/` does NOT make it discoverable. You must also create the symlink. See the recipe below.

**Sanity-check for broken symlinks** (run after any rename or skill removal):

```bash
find ~/.claude/skills/ -maxdepth 1 -type l ! -exec test -e {} \; -print
```


## Skill-writing conventions

- **Frontmatter `description` is everything for triggering.** Lead with "This skill should be used when…" or an equivalent third-person statement. Include concrete example trigger phrases — that's what the dispatcher matches against. Add an explicit negative case ("Does NOT fire on…") when the surface is easy to confuse with a sibling skill.
- **Keep the description specific.** Soft cap ~500 chars, hard cap 1024. Vague descriptions over-trigger and erode trust in the skill system.
- **SKILL.md body ≤ ~3000 words.** Anything heftier (full reference docs, large config schemas, big tables) goes in `references/` and is loaded only when the agent needs it. Progressive disclosure is the rule.
- **No `Read`ing other skills' `SKILL.md`.** If two skills need shared facts, either duplicate the fact or put it in this `CLAUDE.md`.
- **Env-var defaults pattern.** Skills that talk to remote hosts use `${SKILL_HOST:-default-alias}`-style env vars and document persistence via `~/.claude/settings.json`'s `env` block (which Claude Code injects into every spawned shell).

## Host targets (the steamy / dookie / WillyNet bit)

Most skills here drive Jacob's homelab over SSH. The default ssh aliases and what they reach:

| Alias | Reaches | Default for which skills |
|---|---|---|
| `steamy-wsl` | Jacob's actual desktop — Win11 + WSL2 Ubuntu on the RTX 4070 box. **He works on this 99% of the time.** | `screenshots`, `clipboard`, `nircmd`, `chrome`, `sysinternals` |
| `dookie` | Debian VM (running on tootie) — dev / AI / MCP hub. Hosts the dockur/windows sandbox container. | `winbox` (via `http://dookie:8006`), homelab-map MCP servers |
| `tootie` | Unraid NAS (i7-13700K, 128GB, port 29229 for ssh) — main app server | rclone, things touching `/mnt/user/*` |

**Override at session time** via `~/.claude/settings.json`:

```json
{ "env": { "SCREENS_HOST": "workbox", "CLIPBOARD_HOST": "workbox" } }
```

…or one-shot inline: `SCREENS_HOST=workbox <cmd>`.

For the full host inventory (six devices, IPs, what runs where, MCP server map, storage layout, backup chains, known issues), use the **`homelab-map`** skill — it triggers on any named device or `WillyNet`.

## Known cross-skill quirks

- **`agent-browser keyboard type` is a no-op against noVNC canvases.** Use the `winbox_type` per-char `press` loop. Documented in `winbox`.
- **NirCmd `clipboard set` is ANSI / CP-1252 only** — emoji and CJK get mangled. The `clipboard` skill's `clip.sh` auto-routes Unicode through PowerShell's `Set-Clipboard` via a UTF-8 temp file.
- **dockur/windows `\\host.lan\Data` SMB share is install-time only.** Once Windows finishes setup, the share disappears. Don't rely on it for ongoing file transfer to/from the winbox.
- **Chrome CDP only sees events after `Network.enable`/`Runtime.enable` were sent on the current connection.** History isn't replayed. The `chrome` skill's `cdp-call.ps1` is one-shot per call; for live event streams it needs extension.
- **`agent-browser` is a global npm CLI** — `npm i -g agent-browser`, run `agent-browser skills get core` for its built-in usage guide. Referenced by the `winbox` and `chrome` skills.

## Working on this repo

- It's a git repo (`main` branch). Skills get committed as their own dirs.
- Background isolation guard is **disabled** in `.claude/settings.json` (`"worktree": {"bgIsolation": "none"}`) so background sessions can edit in place without `EnterWorktree`.
- `additional working dir`: `~/workspace/unraid-api` is exposed alongside this one for cross-repo session work.

## Adding a new skill

1. `mkdir -p src/skills/<name>/{scripts,references}` (drop the subdirs you don't need)
2. Write `src/skills/<name>/SKILL.md` with frontmatter (`name:` matching dir, `description:` with triggers)
3. Write `src/skills/<name>/README.md` (no frontmatter — overview, when-to-invoke, files, companion skills)
4. Write `src/skills/<name>/CHANGELOG.md` (seed with today's date and an "Added — initial release" entry)
5. Validate with `validate-skill` (or `vibin:validate-skill`) — checks frontmatter, trigger phrases, structure
6. Run `plugin-dev:skill-reviewer` for deeper convention review before publishing
7. **Wire it up:** `ln -sf ~/.agents/src/skills/<name> ~/.claude/skills/<name>`
8. Open a fresh session — new skills appear at session start, not mid-session

## Renaming or removing a skill

The symlink farm doesn't auto-clean. After any rename, the old symlink dangles and the new dir has no symlink at all:

```bash
# rename
mv ~/.agents/src/skills/<old> ~/.agents/src/skills/<new>
sed -i "s/^name: <old>$/name: <new>/" ~/.agents/src/skills/<new>/SKILL.md
rm ~/.claude/skills/<old>
ln -sf ~/.agents/src/skills/<new> ~/.claude/skills/<new>

# remove
rm -rf ~/.agents/src/skills/<name>
rm ~/.claude/skills/<name>
```

Then re-run the broken-symlink sanity check from "Skill discovery" above.


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
