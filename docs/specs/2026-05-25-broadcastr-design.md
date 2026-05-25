# Broadcastr — Design Spec

**Status:** Draft — pending review
**Date:** 2026-05-25
**Plugin path:** `plugins/broadcastr/`
**Author:** Jacob Magar
**Marketplaces:** Claude Code + Codex (asymmetric — see [Codex story](#codex-story))

## Problem

Multiple Claude / Codex agents frequently work concurrently on the same repo (and across repos in the homelab). Each agent is blind to what the others are doing — commits, plan edits, branch changes, container restarts, CI failures all happen invisibly. The user has to manually relay state between agents, and agents redo work that another agent already finished or step on each other.

## Goal

A real-time, *automatic* activity broadcast so every running agent sees what every other agent (and the user) is doing in the repo and across the homelab. Agents should not have to remember to emit; events should be captured automatically wherever possible.

## Non-goals

- Not a chat system. No agent-to-agent conversation. Broadcasts are one-way: facts about what just happened.
- Not a coordination primitive. Broadcastr informs; it does not lock, queue, or arbitrate.
- Not a persistent audit log. The bus is best-effort and short-lived; long-term history lives in git / beads / syslog.
- Not durable across machine reboots in v1. (The bus file survives, but events from before the current session start are skipped by the feed monitor.)

## Architecture

Three layers, glued by a shared JSONL bus:

```
emitters → bus (JSONL) → consumers
   |                        |
   |                        ├── agent monitor (Claude: in-session notifications)
   |                        ├── userPromptSubmit hook (Codex: per-turn injection)
   |                        └── apprise gateway (alert-tier only → phone)
   |
   ├── claude code hooks (SessionStart, Stop, PostToolUse on Bash)
   ├── git hooks (post-commit, pre-commit, pre-push, post-checkout, post-merge)
   ├── inotify monitors (long-running, watch plan/session/agent dirs)
   └── manual cli (broadcastr emit ...)
```

The bus is append-only JSONL. Every emitter writes events; every consumer tails events. Emitters and consumers are independent — adding a new emitter is purely additive.

## Bus layout

Two parallel bus files. Producers write both (configurable via `BROADCASTR_GLOBAL_FEED`); each consumer chooses which to tail.

| File | Path | Purpose |
|---|---|---|
| Per-repo | `${CLAUDE_PROJECT_DIR}/.broadcastr/events.jsonl` | Repo-scoped activity. Gitignored. |
| Global | `${BROADCASTR_HOME:-~/.claude/broadcastr}/events.jsonl` | Cross-repo homelab activity. Carries a `repo` field for filtering. |

**Why not `${CLAUDE_PLUGIN_DATA}` for the global bus?** `CLAUDE_PLUGIN_DATA` is per-plugin-id and not shared between Claude and Codex installs of the same plugin. The global bus must be reachable from both, so it lives at a stable, platform-neutral path.

**Atomicity:** writes are line-oriented JSONL appended with `O_APPEND`, which POSIX guarantees is atomic for writes under `PIPE_BUF` (4096 bytes on Linux). All our events are well under that limit.

**Rotation:** lazy size-based, performed inside `emit.sh` before each write. When the bus exceeds `BROADCASTR_BUS_MAX_BYTES` (default 5 MB), `emit.sh` atomically rotates `events.jsonl → events.jsonl.1`, shifts older rotations (`.1→.2`, `.2→.3`, drops anything beyond `BROADCASTR_BUS_RETAIN`, default 3), and creates a fresh empty `events.jsonl`. Per-repo and global buses rotate independently. Consumers using `tail -F` follow files by name and reopen after rotation automatically. Cost per emit: one `stat` call (rotation itself happens roughly every several thousand events at default thresholds).

**History on resume:** the agent feed monitor skips events older than its own startup time, so neither rotation nor session resume replays history.

## Event schema

One JSON object per line. The schema lives at `plugins/broadcastr/schema.json` and is shared by every emitter and the validator in the CLI.

```json
{
  "ts": "2026-05-25T22:59:00.123Z",
  "id": "evt_01HXYZ4K5J9N",
  "tier": "info",
  "category": "commit",
  "source": "git-hook",
  "emitter": {
    "session_id": "abc-123-def",
    "agent": "claude-code",
    "host": "dookie",
    "user": "jmagar"
  },
  "repo": "/home/jmagar/.agents",
  "branch": "main",
  "summary": "commit a1b2c3d: Add broadcastr plugin scaffold",
  "data": { "sha": "a1b2c3d", "files_changed": 7 }
}
```

### Required fields

| Field | Type | Notes |
|---|---|---|
| `ts` | ISO-8601 UTC | RFC 3339 with millisecond precision |
| `id` | string | ULID with `evt_` prefix; unique across all events |
| `tier` | `"info"` \| `"alert"` | drives apprise routing |
| `category` | string | one of the 14 fixed categories below |
| `source` | string | `claude-hook` \| `git-hook` \| `inotify` \| `poll` \| `cli` |
| `emitter.session_id` | string \| null | Claude/Codex session id when known |
| `emitter.agent` | string | `claude-code` \| `codex` \| `user` |
| `emitter.host` | string | hostname |
| `emitter.user` | string | `$USER` |
| `repo` | string | absolute path to repo root |
| `summary` | string | single-line human-readable; **this is what consumers display** |
| `data` | object | category-specific payload (free-form) |

### Category enum

| Category | Tier (default) | Source | Phase |
|---|---|---|---|
| `agent-presence` | info | claude-hook + inotify | v1 |
| `commit` | info | git-hook | v1 |
| `pre-commit` | info (pass) / alert (fail) | git-hook | v1 |
| `push` | info (success) / alert (fail) | git-hook | v1 |
| `plan` | info | inotify | v1 |
| `bead` | info | claude-hook (Bash match) | v1 |
| `session-doc` | info | inotify | v1 |
| `plan-exec` | info | inotify (content match) | v1 |
| `branch` | info | git-hook | v1 |
| `stash` | info | claude-hook (Bash match) | v1 |
| `pr` | info (opened/merged) / alert (failed checks) | poll (`gh pr list`) | v2 |
| `cargo` | info (start/ok) / alert (fail) | claude-hook (Bash match) + optional wrapper | v2 |
| `container` | info (start) / alert (down/restart-loop) | poll (`docker events`) | v2 |
| `ci` | info (queued/run) / alert (fail) | poll (`gh run list`) | v2 |

## Producers (v1)

All producers invoke a single helper:

```
${CLAUDE_PLUGIN_ROOT}/scripts/emit.sh <category> <tier> <summary> [--data <json>]
```

`emit.sh` is the *only* code path that writes to the bus. It:
1. Generates ULID and timestamp.
2. Resolves emitter context: `CLAUDE_SESSION_ID`, `CODEX_SESSION_ID`, `HOSTNAME`, `USER`.
3. Atomically appends one JSONL line to the per-repo bus.
4. If `BROADCASTR_GLOBAL_FEED=1` (default), atomically appends to the global bus too.
5. No-ops silently if `BROADCASTR_DISABLED=1`.

### 1. Claude Code hooks — `plugins/broadcastr/hooks/hooks.json`

| Event | Action |
|---|---|
| `SessionStart` | emit `agent-presence` (joined) with session id + cwd |
| `Stop` | emit `agent-presence` (left) |
| `PostToolUse` matcher `Bash` | classify command via regex (`bd create\|update\|close` → `bead`; `git stash\|git stash pop` → `stash`); emit if matched, otherwise no-op |

### 2. Git hooks — installed by `broadcastr:install-hooks` skill

The skill drops idempotent shim hooks into `.git/hooks/`. Each shim emits and then chains to any pre-existing hook of the same name (preserved as `<hook>.broadcastr-prev` if one existed before install).

| Hook | Event(s) emitted |
|---|---|
| `post-commit` | `commit` with sha + files-changed count |
| `pre-commit` | `pre-commit` start; runs original; emits pass/fail |
| `pre-push` | `push` with target ref + remote; emits success/fail after the actual push |
| `post-checkout` | `branch` with prev → new ref, distinguishing branch/worktree/file checkout via the third arg |
| `post-merge` | `branch` (merge subtype) with merged ref |

### 3. inotify monitors — `plugins/broadcastr/monitors/monitors.json`

Three long-running monitors, declared as plugin monitors so Claude Code starts them at session start. They are *not* consumers of the bus — they are producers of events from filesystem activity. (Claude consumers are described in the next section.)

| Monitor name | Watches | Emits |
|---|---|---|
| `broadcastr-plans` | `${CLAUDE_PROJECT_DIR}/docs/plans`, `${CLAUDE_PROJECT_DIR}/docs/superpowers/plans` | `plan`, `plan-exec` (on content marker change) |
| `broadcastr-sessions` | `${CLAUDE_PROJECT_DIR}/docs/sessions` | `session-doc` |
| `broadcastr-cross-agent` | `~/.claude/projects/`, `~/.codex/sessions/` | `agent-presence` (cross-editor detection, deduped by session id with the SessionStart hook) |

### 4. Manual CLI

```
broadcastr emit <category> <tier> <summary> [--data <json>]
```

Symlinked into `~/.local/bin` by the `broadcastr:install-hooks` skill on first run (or invokable as `${CLAUDE_PLUGIN_ROOT}/bin/broadcastr` directly). Used when an agent wants to broadcast something not covered by automatic emitters (e.g., "I'm about to nuke `target/`").

## Consumers

### Claude Code — agent feed monitor

`plugins/broadcastr/monitors/monitors.json` declares (alongside the inotify producers):

```json
{
  "name": "broadcastr-feed",
  "command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/tail-bus.sh",
  "description": "Live homelab activity feed (broadcastr)"
}
```

`tail-bus.sh`:
1. Establishes a startup timestamp (so we don't replay history on session resume).
2. `tail -F` on the per-repo bus, and on the global bus if `BROADCASTR_GLOBAL_FEED=1`.
3. Parses each line; **drops** events where `emitter.session_id == $CLAUDE_SESSION_ID` (self-suppression).
4. Drops events with `ts < startup`.
5. Drops events whose category is in `$BROADCASTR_MUTE` (comma-separated user override).
6. Formats each remaining event as a single line: `[<tier>] <category> · <summary> · <emitter.agent>@<host>`.
7. Writes to stdout (which Claude Code surfaces as a notification per line).
8. On `SIGTERM`, closes its `tail` child cleanly.

### Codex — `UserPromptSubmit` hook injection

Codex doesn't have a monitor-equivalent that auto-pushes stdout to the agent. Instead, on every user prompt:

```json
// .codex-plugin/plugin.json (excerpt)
{
  "hooks": {
    "UserPromptSubmit": [
      { "command": ["${CLAUDE_PLUGIN_ROOT}/scripts/codex-prompt-inject.sh"] }
    ]
  }
}
```

`codex-prompt-inject.sh`:
1. Reads `${BROADCASTR_HOME:-~/.claude/broadcastr}/sessions/<session-id>/last-prompt-ts` (or session start if absent). Lives outside `CLAUDE_PLUGIN_DATA` because that path is per-plugin-id and not stable across Claude / Codex installs of the same plugin.
2. Reads all events from the bus with `ts > last-prompt-ts` and `emitter.session_id != $CODEX_SESSION_ID`.
3. Prints them as a system-context block to stdout (which Codex injects into the next prompt).
4. Updates `last-prompt-ts` to now.

Outcome: Codex agents see new events at most one turn late, with zero polling cost.

### Apprise gateway — alert tier only

```json
{
  "name": "broadcastr-alerts",
  "command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/alert-gateway.sh",
  "description": "Routes alert-tier events to apprise"
}
```

`alert-gateway.sh` tails the global bus, filters for `tier == "alert"`, and shells out to `apprise --tag <user_config.apprise_tag> --body <summary>`. One notification per alert. Gated behind `user_config.apprise_enabled` (default `true`).

## Asymmetries between Claude and Codex

| Capability | Claude Code | Codex |
|---|---|---|
| Hooks (SessionStart, Stop, UserPromptSubmit, PostToolUse) | ✓ | ✓ |
| Plugin monitors (real-time stdout → notifications) | ✓ | ✗ |
| Agent-side feed delivery | Live via monitor | Per-turn via UserPromptSubmit hook |
| Apprise gateway | ✓ (runs from Claude's monitor) | Inherited (gateway runs once per host, not per agent) |

The bus and emitters are identical across both. Only the *consumer* side differs.

## Codex story

(Cross-referenced from the asymmetry table.)

Codex's plugin runtime has no equivalent of Claude's monitor → in-session notifications. We considered three options:

- **(A) Read-on-demand** — agent runs `broadcastr recent --since=10m` when relevant. Lowest effort, but Codex agents need to remember to check.
- **(B) UserPromptSubmit injection** — selected. Hook auto-injects new events on every user prompt. Per-turn batching, zero polling.
- **(C) Background task + per-turn check** — spawn `tail -F` as a Codex background task and read its output file each turn. Mechanically equivalent to (B), with extra moving parts and job lifecycle to manage.

**(B)** wins because it gives Codex the same UX as Claude (events show up automatically in-session) while honoring Codex's actual delivery model.

## Layout

```
plugins/broadcastr/
├── .claude-plugin/plugin.json       ← Claude manifest; requires v2.1.105+ for monitors
├── .codex-plugin/plugin.json        ← Codex manifest; hooks-only
├── README.md
├── CHANGELOG.md
├── schema.json                       ← event schema (shared)
├── hooks/
│   └── hooks.json                    ← Claude hooks: SessionStart, Stop, PostToolUse(Bash)
├── monitors/
│   └── monitors.json                 ← feed + alert-gateway + 3 inotify producers
├── skills/
│   ├── broadcastr/                   ← user-facing: how to read the feed, mute categories, emit manually
│   │   ├── SKILL.md
│   │   ├── README.md
│   │   └── CHANGELOG.md
│   └── broadcastr-install-hooks/     ← idempotent per-repo git-hook installer
│       ├── SKILL.md
│       ├── README.md
│       ├── CHANGELOG.md
│       └── scripts/install-git-hooks.sh
├── commands/
│   └── broadcastr.md                 ← /broadcastr slash: status, recent N events, toggle global
├── bin/
│   └── broadcastr                    ← CLI shim (emit, tail, status, recent, mute)
├── scripts/
│   ├── emit.sh                       ← canonical event writer (atomic JSONL append, dual bus)
│   ├── tail-bus.sh                   ← Claude feed monitor entry
│   ├── alert-gateway.sh              ← apprise fan-out
│   ├── codex-prompt-inject.sh        ← Codex UserPromptSubmit injection
│   ├── watch-plans.sh                ← inotify producer for plan dirs
│   ├── watch-sessions.sh             ← inotify producer for docs/sessions
│   ├── watch-agents.sh               ← inotify producer for ~/.claude & ~/.codex
│   └── git-hooks/                    ← templates installed into .git/hooks/
│       ├── post-commit
│       ├── pre-commit
│       ├── pre-push
│       ├── post-checkout
│       └── post-merge
└── docs/                              ← optional in-plugin reference (architecture diagram, schema cheatsheet)
```

## User configuration

Declared in `.claude-plugin/plugin.json` (`userConfig`):

| Key | Type | Default | Description |
|---|---|---|---|
| `apprise_enabled` | boolean | `true` | Fan out `alert`-tier events to apprise |
| `apprise_tag` | string | `"broadcastr"` | Apprise routing tag |
| `global_feed` | boolean | `true` | Tail the global bus in addition to the per-repo bus |
| `mute_categories` | string (multiple) | `[]` | Categories to drop from the agent feed (e.g., `["plan-exec"]` if too noisy) |
| `bus_max_bytes` | number | `5242880` | Rotate the bus when it exceeds this size (5 MB default) |
| `bus_retain` | number | `3` | Number of rotated bus files to keep |

Exposed at runtime as `${user_config.*}` substitution and as `CLAUDE_PLUGIN_OPTION_*` env vars to all scripts.

## Failure modes

| Failure | Effect | Handling |
|---|---|---|
| Bus file missing | `emit.sh` creates it on first write (`mkdir -p`, `touch`) | Self-healing |
| inotifywait not installed | inotify monitors fail at startup | `broadcastr:install-hooks` skill checks and warns at install; events from FS sources go silent (no crash) |
| `apprise` CLI missing | `alert-gateway.sh` logs and skips | Setting `apprise_enabled=false` disables the monitor entirely |
| Stale `.git/hooks/<hook>.broadcastr-prev` from old install | Hook chain still runs prev; uninstall restores it | `broadcastr:install-hooks` is idempotent and detects existing shims |
| Bus grows unbounded | Disk creep | Lazy size-based rotation in `emit.sh` (5 MB × 3 rotations = ~20 MB cap per bus); see [Bus layout → Rotation](#bus-layout) |
| Two emitters race on `O_APPEND` | Both lines written atomically, in arbitrary order | Acceptable; ordering within sub-millisecond is undefined by design |
| Self-suppression misfires (session id absent) | Agent sees own event | Acceptable for v1; tier `info`, low cost |

## Out-of-scope for v1

- v2 polling emitters: PR status (`gh pr list`), CI/CD (`gh run list`), container events (`docker events`), cargo build watching.
- Web UI / Aurora dashboard for the global feed.
- TUI consumer (`broadcastr watch`).
- Multi-host bus sync (right now the global bus is per-host; cross-host would need a shared mount or a small relay).
- Encrypted bus (currently `chmod 600`, no encryption at rest).

## Open questions

None blocking. Decisions logged above.

## Success criteria

1. Two Claude Code agents in two terminals on the same repo: agent A commits; agent B sees a notification line about it within one second.
2. A Codex agent in a third terminal sees the same commit reflected in the system context of its next prompt.
3. A `git push` failure produces an apprise notification on the user's phone.
4. Stopping any of the agents does not leave dangling processes.
5. Installing broadcastr into a repo with existing `.git/hooks/pre-commit` does not break the existing hook; uninstalling restores it.
