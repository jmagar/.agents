# Changelog

## [0.1.3] - 2026-05-27
### Changed
- `tail-bus.sh` `format_line`: full output format redesign:
  - Removed `broadcastr` label from every line — the emoji prefix is sufficient
  - Removed `@host` — no multi-device routing yet
  - Replaced text category tags with glyphs: `👤` presence, `🌿` git, `📝` docs, `🎯` beads
  - Related categories share one glyph (commit/push/pre-commit/branch/stash → `🌿`; session-doc/plan/plan-exec → `📝`)
  - Summaries always lead with agent name: "Claude joined", "Claude saved: ...", "Claude's push FAILED · branch"
  - Bead action verbs are past-tense (closed/created/updated/reopened)
  - Final shape: `📡/🚨 GLYPH[project] Agent action`

## [0.1.2] - 2026-05-27
### Changed
- `tail-bus.sh` `format_line`: repo basename now appended — `project@host` instead of `@host`. Every event now shows which repo it came from.

## [0.1.1] - 2026-05-27
### Changed
- `tail-bus.sh` `format_line`: output now uses `📡 broadcastr [category] summary · project@host` format instead of `[i] category summary @host`. The previous syslog-style format caused Claude to paraphrase events as "Routine presence event — no action needed" instead of relaying them verbatim.
- `🚨` prefix for alert-tier events instead of `[!]`.
- Global `CLAUDE.md`: added explicit instruction to relay broadcastr-feed monitor output verbatim.

## [0.1.0] - 2026-05-25
- Initial release.
