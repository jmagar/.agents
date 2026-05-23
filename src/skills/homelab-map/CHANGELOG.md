# Changelog

All notable changes to this skill are recorded here. Format roughly follows [Keep a Changelog](https://keepachangelog.com/).

## 2026-05-23

### Added
- Added `scripts/generate-homelab-report.py` to generate `~/.homelab/homelab.md` from live SSH, Docker, ZFS, Unraid, and SWAG config checks.
- Added a static report template at `references/homelab.md`.

### Changed
- Converted `references/homelab.md` from a manually maintained snapshot into a static report template.
- Changed the generator default output to `~/.homelab/homelab.md` so volatile runtime snapshots do not dirty the repository.
- Updated `SKILL.md` and `README.md` to distinguish the repo template from the generated runtime report.

## 2026-05-17

### Added
- Initial CHANGELOG.
