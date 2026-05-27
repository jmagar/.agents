# Changelog

## [0.1.1] - 2026-05-26
- Disabled the Claude `PostToolUse` Bash classifier hook. Bead and stash activity can be observed through syslog instead, avoiding a broadcastr hook invocation after every Bash tool call.
- Made monitor scripts fall back to their current working directory when Claude does not provide `CLAUDE_PROJECT_DIR`.

## [0.1.0] - 2026-05-25
- Initial release. Per-repo + host-global JSONL bus, Claude hooks (SessionStart/Stop/PostToolUse-Bash), git hooks (post-commit, pre-commit, pre-push, post-checkout, post-merge), inotify watchers (plans, sessions), feed monitor with self-suppression, apprise alert gateway. Claude Code only — Codex deferred.
