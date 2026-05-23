---
name: save-to-md
description: Save session documentation to a markdown file with full context — date, branch, HEAD, session ID, and git state pre-injected. Use when the user says "save session", "save to md", "document this session", "write up what we did", "save session notes", or asks to capture the current conversation as a session log. Also invoked automatically by quick-push after a successful push.
allowed-tools: Write, Read, Bash
argument-hint: [path]
---

## Context

- Date: !`TZ=America/New_York date '+%Y-%m-%d %H:%M:%S EST'`
- Repo: !`git remote get-url origin`
- Branch: !`git branch --show-current`
- HEAD: !`git rev-parse --short HEAD`
- Recent commits: !`git log --oneline -5`
- Files currently dirty: !`git status --short`
- Files in recent commits: !`git log --oneline --name-only -10`
- Transcript: !`ls -t ~/.claude/projects/$(pwd | sed 's|/|-|g')/*.jsonl 2>/dev/null | head -1`
- Active plan: !`cat .claude/current-plan 2>/dev/null || echo "none"`
- Working directory: !`pwd`
- Repo root: !`git rev-parse --show-toplevel 2>/dev/null || pwd`
- Worktree: !`git worktree list | grep $(pwd) | head -1`
- Active PR: !`gh pr view --json number,title,url 2>/dev/null || echo "none"`
- Beads recent issues: !`bd list --all --sort updated --reverse --limit 100 --json 2>/dev/null || echo "[]"`
- Beads recent interactions: !`tail -200 .beads/interactions.jsonl 2>/dev/null || echo "none"`
- Registered worktrees: !`git worktree list --porcelain 2>/dev/null || echo "none"`
- Local branches: !`git branch -vv 2>/dev/null || echo "none"`
- Remote branches: !`git branch -r -vv 2>/dev/null || echo "none"`
- Plans: !`find docs/plans -maxdepth 2 -type f 2>/dev/null | sort || echo "none"`

# Save Session Documentation

Document the **entire conversation session** (not just recent work) as a markdown file at `$ARGUMENTS`. If the injected `Transcript` path above is non-empty, read it to recover the full session (the current context window may be truncated). If no path is provided, save to `docs/sessions/YYYY-MM-DD-description.md` under the repo root.

Path rules:
- Relative paths resolve from the repo root (not CWD).
- Keep this workflow in-repo. If the resolved target is outside the repo root, stop and report the path issue.
- Check whether the target directory exists (`[ -d <dir> ]`) before creating it — only run `mkdir -p` if the check fails.
- If the target filename already exists, do not overwrite. Append a suffix like `-v2`, `-v3`, etc.

## Repository Maintenance Pass

Before writing the session note, perform a repo maintenance pass and document exactly what happened. Keep this pass evidence-driven and safe; do not hide skipped, blocked, or uncertain cleanup.

1. **Plans**: Find completed plan files under `docs/plans/` and move only clearly completed plans to `docs/plans/complete/`. Create `docs/plans/complete/` only if needed. Do not move active, partial, draft, or ambiguous plans; list them in **Open Questions** or **Next Steps**.
2. **Beads**: Run the relevant `bd` reads before changing tracker state. Create, edit, comment on, claim, assign, or close all beads that are directly relevant to the session and remaining work. Close completed beads only when the work and verification are observed. Create follow-up beads for known remaining work instead of burying it only in prose.
3. **Worktrees and branches**: Inspect `git worktree list --porcelain`, local branches, remote branches, and merge ancestry before cleanup. Remove stale worktrees or branches only when they are proven safe, for example merged into the protected base branch or otherwise explicitly obsolete. Do not delete dirty worktrees, unmerged branches, unknown backup refs, active PR branches, or anything with unclear ownership; document why each was left alone.
4. **Stale docs**: Review documentation touched by or contradicted by the session. Update stale docs when the current implementation or workflow proves them wrong. If the stale-doc pass is too broad to complete safely, create/update beads and list precise docs follow-ups.
5. **Transparency**: Record every maintenance action, no-op, skipped item, blocked item, and assumption in the session note. Include the command or evidence used for each cleanup decision.

## Documentation Requirements

Start the file with a metadata block populated from the injected context above:

```yaml
date: YYYY-MM-DD HH:MM:SS EST
repo: <remote URL>
branch: <current branch>
head: <HEAD commit SHA>
plan: <path/to/plan.md> (if applicable, otherwise omit)
session id: <UUID filename of the transcript, e.g. cef54ead-b02d-4c3e-a833-a8672fa20523> (omit if transcript injection was empty)
transcript: <full path to the .jsonl transcript file> (omit if transcript injection was empty)
working directory: <pwd>
worktree: <worktree path if applicable, otherwise omit>
pr: <PR number, title, and URL if applicable, otherwise omit>
beads: <IDs of beads created, closed, edited, or worked on during this session; omit only if none>
```

Then include these sections:
1. **User Request**: The original prompt or goal that initiated the session — one or two sentences verbatim or paraphrased
2. **Session Overview**: Brief summary of what was accomplished
3. **Sequence of Events**: Chronological breakdown of major activities (no timestamps — order only)
4. **Key Findings**: Important discoveries with file paths and line numbers where relevant
5. **Technical Decisions**: Reasoning behind implementation choices
6. **Files Changed**: List every file created, modified, renamed, or deleted. Prefer a table with `status | path | previous path | purpose | evidence`, where `status` is `created`, `modified`, `renamed`, or `deleted`
7. **Beads Activity**: List every bead created, closed, edited, claimed, assigned, commented on, or otherwise worked during the session. Include bead ID, title, action(s), final status, and why it mattered. Use the injected `Beads recent issues`, `Beads recent interactions`, transcript, and command output; do not omit a bead just because it is already closed
8. **Repository Maintenance**: Summarize completed-plan moves, bead updates, worktree/branch cleanup, stale-docs updates, no-ops, skipped items, blocked items, and the evidence behind each decision
9. **Tools and Skills Used**: List every tool category used during the session: shell commands, file tools, MCP servers/tools, skills, plugins, subagents/agents, browser tools, and external CLIs. Include the purpose for each category and any issues encountered, including failures, degraded behavior, missing permissions, bad outputs, retries, and workarounds. If only shell/file reads were used, state that explicitly and list whether any issues were observed
10. **Commands Executed**: Critical bash commands and their results
11. **Errors Encountered**: What failed, root cause, and how it was resolved — omit if no errors occurred
12. **Behavior Changes (Before/After)**: User-visible or system-visible behavior changes caused by this session
13. **Verification Evidence**: Table with `command | expected | actual | status` — omit if no verification commands were run
14. **Risks and Rollback**: Concise risk notes and rollback path for non-trivial changes — omit if no risk
15. **Decisions Not Taken**: Alternatives considered but rejected, with brief rationale — omit if none
16. **References**: Docs, PRs, issues, or URLs consulted during the session — omit if none
17. **Open Questions**: Unresolved items or assumptions that need follow-up — omit if none
18. **Next Steps**: Clear, actionable guidance for how to proceed. Distinguish unfinished work from this session, follow-on tasks not yet started, blocked tasks, and recommended immediate next commands

After writing the file, print the final absolute path so callers (e.g., `quick-push`) can reference it.

Content quality rules:
- Facts only. Do not infer values that were not observed in tool/command output.
- If something is uncertain, place it in **Open Questions** instead of stating it as fact.
- Treat Beads activity as mandatory session context. If no bead activity occurred, state `No bead activity observed`; otherwise list every observed bead action even if it seems administrative.
- Treat repository maintenance as mandatory session closeout context. If no maintenance action was needed or safe, state that explicitly and give the observed evidence.
- Do not present cleanup as complete unless plan files, beads, worktrees/branches, and stale docs were all checked or explicitly marked out of scope with a reason.
- Keep sections concise (target max 5 bullets per section), but exceed when needed to preserve material implementation details, critical evidence, or safety context.
- Use file:line references (e.g., `server.ts:45`) for code-specific findings.
