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

# Save Session Documentation

Document the **entire conversation session** (not just recent work) as a markdown file at `$ARGUMENTS`. If the injected `Transcript` path above is non-empty, read it to recover the full session (the current context window may be truncated). If no path is provided, save to `docs/sessions/YYYY-MM-DD-description.md` under the repo root.

Path rules:
- Relative paths resolve from the repo root (not CWD).
- Keep this workflow in-repo. If the resolved target is outside the repo root, stop and report the path issue.
- Check whether the target directory exists (`[ -d <dir> ]`) before creating it — only run `mkdir -p` if the check fails.
- If the target filename already exists, do not overwrite. Append a suffix like `-v2`, `-v3`, etc.

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
6. **Files Changed**: List every file created, modified, renamed, or deleted, with the purpose of each change
7. **Beads Activity**: List every bead created, closed, edited, claimed, assigned, commented on, or otherwise worked during the session. Include bead ID, title, action(s), final status, and why it mattered. Use the injected `Beads recent issues`, `Beads recent interactions`, transcript, and command output; do not omit a bead just because it is already closed
8. **Tools and Skills Used**: List all notable tools, MCP servers, agents, and skills used during the session, with their purpose. Include any and all issues encountered with tools, MCP servers, agents, or skills, including failures, degraded behavior, missing permissions, bad outputs, retries, and workarounds. Omit only if none were used beyond basic shell/file reads
9. **Commands Executed**: Critical bash commands and their results
10. **Errors Encountered**: What failed, root cause, and how it was resolved — omit if no errors occurred
11. **Behavior Changes (Before/After)**: User-visible or system-visible behavior changes caused by this session
12. **Verification Evidence**: Table with `command | expected | actual | status` — omit if no verification commands were run
13. **Risks and Rollback**: Concise risk notes and rollback path for non-trivial changes — omit if no risk
14. **Decisions Not Taken**: Alternatives considered but rejected, with brief rationale — omit if none
15. **References**: Docs, PRs, issues, or URLs consulted during the session — omit if none
16. **Open Questions**: Unresolved items or assumptions that need follow-up — omit if none
17. **Next Steps**: Unfinished work from this session (started but not completed) and follow-on tasks not yet started — distinguish between the two

After writing the file, print the final absolute path so callers (e.g., `quick-push`) can reference it.

Content quality rules:
- Facts only. Do not infer values that were not observed in tool/command output.
- If something is uncertain, place it in **Open Questions** instead of stating it as fact.
- Treat Beads activity as mandatory session context. If no bead activity occurred, state `No bead activity observed`; otherwise list every observed bead action even if it seems administrative.
- Keep sections concise (target max 5 bullets per section), but exceed when needed to preserve material implementation details, critical evidence, or safety context.
- Use file:line references (e.g., `server.ts:45`) for code-specific findings.
