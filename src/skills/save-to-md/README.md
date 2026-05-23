# save-to-md

Save the current Claude session as a markdown file under `docs/sessions/`, pre-injected with full context: date, repo, branch, HEAD, recent commits, dirty files, transcript path, active PR, worktree, recent Beads state, registered worktrees, branches, and plan files.

## What it does

1. Resolves a target path (`$ARGUMENTS` or auto: `docs/sessions/YYYY-MM-DD-description.md`).
2. Refuses to overwrite — appends `-v2`, `-v3` suffixes on conflict.
3. If the injected transcript path is set, reads the raw `.jsonl` to recover the full session (the live context window may be truncated).
4. Performs a repository maintenance pass: moves completed plans to `docs/plans/complete/`, updates relevant beads, safely cleans stale worktrees/branches, and checks for stale docs.
5. Writes a metadata block + numbered sections: what was done, files changed, bead activity, repository maintenance, tools used, errors encountered, next steps, open questions, verification evidence.
6. Facts-only rule — no speculation; ambiguity goes into Open Questions.

The generated session note must list every bead created, closed, edited, claimed, assigned, commented on, or otherwise worked during the session. If no bead activity occurred, it says so explicitly.

The generated session note must also document every repo maintenance action, no-op, skipped item, blocked item, and cleanup decision with evidence. Cleanup is only complete when completed plans, beads, worktrees/branches, and stale docs were checked or explicitly marked out of scope with a reason.

Pairs with `hand-off` — this writes the log; `hand-off` reads it back into a fresh session.

## Invoke

Triggers: "save session", "save to md", "document this session", "write up what we did", "save session notes". Also invoked automatically by `quick-push` after a successful push.

## Files

- `SKILL.md` — agent instructions
