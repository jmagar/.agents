# save-to-md

Save the current Claude session as a markdown file under `docs/sessions/`, pre-injected with full context: date, repo, branch, HEAD, recent commits, dirty files, transcript path, active PR, worktree.

## What it does

1. Resolves a target path (`$ARGUMENTS` or auto: `docs/sessions/YYYY-MM-DD-description.md`).
2. Refuses to overwrite — appends `-v2`, `-v3` suffixes on conflict.
3. If the injected transcript path is set, reads the raw `.jsonl` to recover the full session (the live context window may be truncated).
4. Writes a metadata block + numbered sections: what was done, files modified, errors encountered, next steps, open questions, verification evidence.
5. Facts-only rule — no speculation; ambiguity goes into Open Questions.

Pairs with `hand-off` — this writes the log; `hand-off` reads it back into a fresh session.

## Invoke

Triggers: "save session", "save to md", "document this session", "write up what we did", "save session notes". Also invoked automatically by `quick-push` after a successful push.

## Files

- `SKILL.md` — agent instructions
