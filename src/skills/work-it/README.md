# work-it

End-to-end worktree execution workflow: take a plan file, implement it, verify, open a PR, run cleanup + review sweeps, address review comments, save a session log, and commit/push the final state.

## What it does

1. **Worktree** — isolate the work in a fresh worktree.
2. **Implement** — execute the plan; iterate until tests/lints/build are green. Commit as you go.
3. **PR immediately** — open the PR as soon as it's green so CodeRabbit etc. can start reviewing in parallel.
4. **Cleanup** — `lavra-review` pass.
5. **Three `code_simplifier` passes** — impl files, tests, docs (one pass each).
6. **`pr-review-toolkit`** sweeps for architecture / security / performance issues.
7. **Address PR comments** — via `gh-address-comments` (mandatory resolution tracking).
8. **`vibin:save-to-md`** — capture the session log (after step 7, before step 9's commit).
9. **Final `git add . && commit && push`**.

Completion standard: every item ticked, every thread resolved or explicitly dismissed.

## Invoke

Triggers: "work it", execute a `superpowers:executing-plans` document in a worktree, run a complete review-and-fix loop over all touched files.

## Files

- `SKILL.md` — the workflow + non-negotiables + agent dispatch guidance
- `agents/openai.yaml` — OpenAI runtime metadata
