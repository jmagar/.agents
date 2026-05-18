# Changelog

All notable changes to the `quick-push` skill are recorded here. Format roughly follows [Keep a Changelog](https://keepachangelog.com/).

## [0.1.1] - 2026-05-17
- Concretized step 2.7 version-sync verification: replaced hand-wavy "search for stale old-version references" with a concrete `git grep -F "<old_version>"` command across common manifest/doc extensions.
- Clarified step 3 / step 4 sequencing: changelog updates in step 3 document *prior* commits; this push's own entry is amended in after step 4's commit lands (the SHA isn't known until then).
- Added README.

## [0.1.0] - Initial
- Initial skill version.
