# `~/.agents/` — Jacob's skill workshop

This directory holds **handwritten Claude Code skills** that ride along on every session. They're not a published plugin — just a personal kit Claude can reach for whenever a relevant prompt comes in. Each skill is a self-contained subdirectory under `skills/`.

## Layout

```
~/.agents/
├── CLAUDE.md           ← you are here
├── skills/             ← all skills live here, one dir per skill
│   ├── <name>/
│   │   ├── SKILL.md    ← required: frontmatter + body
│   │   ├── README.md   ← human-facing overview (no frontmatter)
│   │   ├── CHANGELOG.md ← Keep-a-Changelog style
│   │   ├── scripts/    ← any helper scripts (bash, ps1, etc.)
│   │   └── references/ ← long reference docs loaded on-demand
│   └── ...
├── plugins/            ← scratch space for plugin experiments
└── docs/
    └── sessions/       ← save-to-md output lives here
```

**Every skill MUST have:** `SKILL.md`, `README.md`, `CHANGELOG.md`. Scripts and references are optional.

## Skill discovery — the symlink farm

Claude Code discovers skills from `~/.claude/skills/<name>/SKILL.md`. The skills in *this* repo live at `~/.agents/skills/<name>/`, and are exposed to Claude via **symlinks** in `~/.claude/skills/`:

```bash
ls -la ~/.claude/skills/ | grep agents
# lrwxrwxrwx ... screenshots -> /home/jmagar/.agents/skills/screenshots
# lrwxrwxrwx ... chrome      -> /home/jmagar/.agents/skills/chrome
# ...
```

**Implication:** writing a SKILL.md under `~/.agents/skills/` does NOT make it discoverable. You must also create the symlink. See the recipe below.

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

1. `mkdir -p skills/<name>/{scripts,references}` (drop the subdirs you don't need)
2. Write `skills/<name>/SKILL.md` with frontmatter (`name:` matching dir, `description:` with triggers)
3. Write `skills/<name>/README.md` (no frontmatter — overview, when-to-invoke, files, companion skills)
4. Write `skills/<name>/CHANGELOG.md` (seed with today's date and an "Added — initial release" entry)
5. Validate with `validate-skill` (or `vibin:validate-skill`) — checks frontmatter, trigger phrases, structure
6. Run `plugin-dev:skill-reviewer` for deeper convention review before publishing
7. **Wire it up:** `ln -sf ~/.agents/skills/<name> ~/.claude/skills/<name>`
8. Open a fresh session — new skills appear at session start, not mid-session

## Renaming or removing a skill

The symlink farm doesn't auto-clean. After any rename, the old symlink dangles and the new dir has no symlink at all:

```bash
# rename
mv ~/.agents/skills/<old> ~/.agents/skills/<new>
sed -i "s/^name: <old>$/name: <new>/" ~/.agents/skills/<new>/SKILL.md
rm ~/.claude/skills/<old>
ln -sf ~/.agents/skills/<new> ~/.claude/skills/<new>

# remove
rm -rf ~/.agents/skills/<name>
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
