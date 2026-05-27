# Changelog

## [0.1.2] - 2026-05-27
### Changed
- `tail-bus.sh` `format_line`: repo basename now appended — `project@host` instead of `@host`. Every event now shows which repo it came from.

## [0.1.1] - 2026-05-27
### Changed
- `tail-bus.sh` `format_line`: output now uses `📡 broadcastr [category] summary · @host` format instead of `[i] category summary @host`. The previous syslog-style format caused Claude to paraphrase events as "Routine presence event — no action needed" instead of relaying them verbatim.
- `🚨` prefix for alert-tier events instead of `[!]`.
- Global `CLAUDE.md`: added explicit instruction to relay broadcastr-feed monitor output verbatim.

## [0.1.0] - 2026-05-25
- Initial release.
