# Changelog

All notable changes to the `save-to-md` skill are recorded here. Format roughly follows [Keep a Changelog](https://keepachangelog.com/).

## [0.1.2] - 2026-05-23
- Added Beads recent issue and interaction context injection.
- Added a mandatory **Beads Activity** section covering beads created, closed, edited, claimed, assigned, commented on, or otherwise worked during the session.
- Updated README to document bead activity capture.

## [0.1.1] - 2026-05-17
- Added `Repo root` to the injected Context block so the "paths resolve from repo root" rule is mechanically executable.
- Added an instruction to read the injected transcript `.jsonl` path so the "document the entire session" rule survives a truncated live context window.
- Dropped the `agent:` field from the metadata block (no injection source — invited fabrication).
- Marked `session id` / `transcript` fields as omit-if-empty so missing injections don't produce fake values.
- Added README.

## [0.1.0] - Initial
- Initial skill version.
