# broadcastr

Real-time activity broadcast across concurrent Claude Code sessions. Captures commits, plan edits, bash commands into a shared JSONL bus; each session sees a notification when other sessions do something interesting.

## Install

This plugin ships via the `~/.agents` marketplace.

## What you see

Once installed, when another Claude session in any repo commits, edits a plan, or fails a push, your session gets a notification line:

```
[info] commit · commit a1b2c3d: Fix auth race · claude-code@dookie
[alert] push · git push failed on feature/x · claude-code@steamy
```

## Components

- Auto-emitters: Claude hooks (SessionStart, Stop, bash-classifier), git hooks (commit, push, branch), inotify watchers (plan files, session docs).
- Feed monitor: tails the bus and surfaces each event as a Claude notification line. Self-suppresses your own session's events.
- Apprise gateway: routes alert-tier events to your phone via apprise.

## Configuration

See `userConfig` in `.claude-plugin/plugin.json`. Override per-session with env vars:
- `BROADCASTR_DISABLED=1` — silence this session entirely
- `BROADCASTR_GLOBAL_FEED=0` — don't tail the global bus
- `BROADCASTR_MUTE=plan-exec,session-doc` — drop these categories

## Skills

- `broadcastr` — user-facing: read the feed, mute, emit manually
- `broadcastr-install-hooks` — idempotent per-repo git-hook installer

## Spec

`docs/specs/2026-05-25-broadcastr-design.md` in the parent repo.
