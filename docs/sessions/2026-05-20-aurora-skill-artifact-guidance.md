---
date: 2026-05-20 18:18:33 EST
repo: https://github.com/jmagar/.agents.git
branch: main
head: 878fd79
working directory: /home/jmagar/.agents
worktree: /home/jmagar/.agents 878fd79 [main]
---

# Aurora skill artifact guidance

## User Request

The user provided an `aurora-design` skill description and asked whether anything from it should be pulled into the existing Aurora design-system skill. After the review, the user asked to make any changes that seemed worthwhile.

## Session Overview

Updated the local Aurora design-system skill to better cover standalone invocation and static visual artifact workflows. Expanded the skill README so future agents can quickly find the right guidance and source files without reading the whole skill first.

## Sequence of Events

1. Inspected `src/skills/aurora-design-system/SKILL.md`, `README.md`, and the reference files.
2. Compared the pasted `aurora-design` guidance against the existing skill.
3. Identified missing coverage around static HTML artifacts, ambiguous standalone invocation, and README discoverability.
4. Edited the skill docs with scoped additions only.
5. Verified the markdown diff, committed the changes, rebased, and pushed to `origin/main`.

## Key Findings

- `src/skills/aurora-design-system/SKILL.md` already covered the core production rules: tokens, type, Lucide icons, Tier 2 panels, content voice, registry usage, and anti-patterns.
- `src/skills/aurora-design-system/README.md` was minimal and did not list the reference files or source repo map.
- The pasted guidance referenced asset and demo directories that were not present in the current skill bundle, so those paths were not copied into the skill docs.

## Technical Decisions

- Added only missing behavior instead of duplicating the pasted quick reference.
- Kept static artifact instructions path-agnostic: copy real brand assets when available, but do not assert specific bundled asset paths that are not present.
- Preserved the existing production React/registry focus while adding guidance for static HTML mocks, slides, prototypes, and design review artifacts.

## Files Modified

- `src/skills/aurora-design-system/SKILL.md` — added standalone invocation behavior and a static artifact workflow.
- `src/skills/aurora-design-system/README.md` — expanded invocation scope, file map, source repo map, and static artifact summary.

## Commands Executed

- `sed -n '1,220p' /home/jmagar/.agents/src/skills/aurora-design-system/SKILL.md` — inspected the existing skill.
- `find /home/jmagar/.agents/src/skills/aurora-design-system -maxdepth 3 -type f | sort` — listed the skill bundle files.
- `rg -n ... /home/jmagar/.agents/src/skills/aurora-design-system` — checked for overlapping guidance.
- `git diff --check -- src/skills/aurora-design-system/SKILL.md src/skills/aurora-design-system/README.md` — verified whitespace and patch hygiene.
- `git commit -m "Update Aurora skill artifact guidance"` — committed the skill update as `878fd79`.
- `git pull --rebase` — confirmed `main` was up to date before pushing.
- `bd dolt push` — attempted Beads sync; no remote was configured, so it skipped.
- `git push` — pushed `878fd79` to `origin/main`.
- `git status --short --branch` — verified the branch was clean and up to date with `origin/main`.

## Behavior Changes (Before/After)

| Area | Before | After |
| --- | --- | --- |
| Ambiguous skill invocation | No explicit instruction for what to ask when the user invokes Aurora without a target. | Ask what surface/artifact is needed and whether output should be production code, static HTML, or a mock/prototype. |
| Static artifacts | Skill focused on React/Next.js and registry consumption. | Skill now covers static HTML artifact creation with fonts, token layer, dark mode, page shell, local assets, and Lucide-style icons. |
| README discoverability | README only named `SKILL.md`. | README now points to references, source repo paths, generated registry output, and gallery demos. |

## Verification Evidence

| command | expected | actual | status |
| --- | --- | --- | --- |
| `git diff --check -- src/skills/aurora-design-system/SKILL.md src/skills/aurora-design-system/README.md` | No whitespace errors. | No output. | Passed |
| `git pull --rebase` | Branch up to date or cleanly rebased. | `Current branch main is up to date.` | Passed |
| `bd dolt push` | Push Beads data if a remote exists. | `No remote is configured — skipping.` | No-op |
| `git push` | Push commit to `origin/main`. | `main -> main` with `b4c143e..878fd79`. | Passed |
| `git status --short --branch` | Clean and up to date. | `## main...origin/main`. | Passed |

## Risks and Rollback

- Risk is low: changes are documentation-only and scoped to one skill.
- Rollback path: `git revert 878fd79` to remove the Aurora skill documentation update.

## Decisions Not Taken

- Did not add the pasted `assets/`, `ui_kits/labby/`, `preview/`, or `_reference/demos/` paths because they were not present in the current skill bundle.
- Did not copy the pasted quick reference wholesale because the existing skill already contains more complete production guidance.

## Open Questions

- Whether the skill bundle should vendor actual Labby/Aurora static assets in the future, rather than only instructing agents to copy assets when available.

## Next Steps

- No started work remains unfinished.
- Optional follow-up: add real branded assets and static HTML templates to the skill bundle if future usage shows static artifact creation is common.
