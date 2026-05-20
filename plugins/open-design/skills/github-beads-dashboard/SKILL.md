---
name: github-beads-dashboard
description: |
  GitHub plus Beads delivery dashboard for a repository. Combines GitHub
  repository health, issues, pull requests, checks, contributors, and recent
  activity with local bd/beads issue state, ready work, blocked work, stale
  work, and sprint/queue health. Use when the brief asks for a GitHub + beads
  dashboard, repo delivery dashboard, maintainer cockpit, PR + issue tracker
  view, or engineering operations dashboard.
triggers:
  - "github beads dashboard"
  - "github + beads dashboard"
  - "repo delivery dashboard"
  - "beads dashboard"
  - "bd dashboard"
  - "maintainer dashboard"
  - "github issue tracker dashboard"
od:
  mode: prototype
  platform: desktop
  scenario: operation
  preview:
    type: html
    entry: index.html
  design_system:
    requires: true
    name: aurora
    sections: [color, typography, layout, components]
  outputs:
    primary: index.html
    secondary:
      - template.html
      - data.json
      - artifact.json
      - provenance.json
  capabilities_required:
    - shell
    - file_write
  example_prompt: "Build a GitHub + Beads dashboard for jmagar/.agents using GitHub PR health and local bd issue state."
---

# GitHub + Beads Dashboard Skill

Create a single-screen engineering operations dashboard that connects GitHub repository state with Beads issue-tracker state. The dashboard should help a maintainer answer: what is shipping, what is blocked, what needs review, what is stale, and whether the repository is healthy.

Use the Aurora operator-console visual language: dark navy workspace, elevated panels, cyan primary accent, rose secondary accent, violet automation accents, muted status colors, compact tables, square status badges, and dense but readable layout. Do not make this look like GitHub.

## Resource map

```text
github-beads-dashboard/
├── SKILL.md
├── example.html
└── references/
    ├── template.html
    ├── example-data.json
    ├── artifact-example.json
    ├── provenance-example.json
    └── README.md
```

## When to use this skill

Use this when the user asks for:

- GitHub + Beads dashboard
- repository delivery dashboard
- PR health plus local issue state
- maintainer cockpit
- release-readiness or queue-health view
- bd/beads operational dashboard

If the user asks for a live or refreshable dashboard, produce `template.html`, `data.json`, `artifact.json`, and `provenance.json`. If they only need a visual prototype, produce a self-contained `index.html`.

## Workflow

1. **Resolve repository and workspace**
   - Parse `owner/repo` from the brief or current Git remote.
   - Resolve the Beads workspace from the current working directory.
   - If no repository can be inferred, ask one concise question for `owner/repo`.
   - If Beads is not initialized, still build the GitHub side and show a clear `beadsUnavailable` state.

2. **Collect GitHub data**
   - Prefer `gh` when available.
   - Repository metadata: `gh repo view OWNER/REPO --json nameWithOwner,description,url,primaryLanguage,licenseInfo,updatedAt,stargazerCount,forkCount,watchers`.
   - Pull requests: `gh pr list --repo OWNER/REPO --state open --json number,title,author,updatedAt,labels,isDraft,reviewDecision,statusCheckRollup`.
   - Issues: `gh issue list --repo OWNER/REPO --state open --json number,title,author,updatedAt,labels,assignees`.
   - Checks: use PR `statusCheckRollup` when available; otherwise record `unknown`.
   - Recent activity: combine newest open PRs and issues, cap at 8 rows.
   - Do not persist tokens, raw HTTP headers, private clone URLs, cookies, or auth config.

3. **Collect Beads data**
   - Run `bd status` for a quick status summary when JSON is not available.
   - Prefer JSON forms when supported by the installed `bd`: `bd ready --json`, `bd list --json`, `bd blocked --json`, `bd stale --json`, `bd stats --json`.
   - If a JSON command is unsupported, fall back to the plain-text command and record the fallback in provenance.
   - Normalize Beads items into: `id`, `title`, `status`, `priority`, `type`, `owner`, `updated`, `blockedBy`, and `sourceUrl` when available.
   - Cap display lists: ready work 6, blocked work 6, stale work 5.

4. **Normalize the joined model**
   - `repository`: identity, description, language, license, URL, updated timestamp.
   - `githubMetrics`: stars, forks, watchers, open issues, open PRs, draft PRs, failing checks, review-needed PRs.
   - `beadsMetrics`: total, open, inProgress, ready, blocked, stale, closed.
   - `delivery`: health label, risk label, release-readiness score, last sync timestamp.
   - `pullRequests`: open PR rows with review/check state.
   - `beadsQueues`: ready, blocked, stale arrays.
   - `recentActivity`: mixed GitHub and Beads rows.
   - `provenance`: command-level source notes and fallbacks.

5. **Apply the Aurora layout**
   - Page shell: dark navy full viewport with fixed left rail and main work area.
   - Header: repo identity, sync timestamp, primary refresh/export actions.
   - KPI row: GitHub health and Beads queue metrics in narrow stat cards.
   - Main grid: PR review/check table on the left, Beads ready/blocked queues on the right.
   - Lower grid: recent activity, delivery risk, and provenance notes.
   - Use stable `data-od-id` values: `sidebar`, `topbar`, `repo-header`, `kpi-strip`, `pr-health`, `beads-queues`, `activity`, `provenance`.

## Data contract

Required top-level fields:

```json
{
  "repository": {},
  "githubMetrics": {},
  "beadsMetrics": {},
  "delivery": {},
  "pullRequests": [],
  "beadsQueues": {
    "ready": [],
    "blocked": [],
    "stale": []
  },
  "recentActivity": [],
  "provenance": []
}
```

Use display-ready strings in the template data. Do not rely on complex template conditionals for status labels; normalize `statusTone`, `checkTone`, and `reviewTone` before rendering.

## Visual rules

- Dark-first only unless the user asks for light mode.
- Use Aurora-like semantic naming in CSS custom properties: `--aurora-page-bg`, `--aurora-panel-medium`, `--aurora-panel-strong`, `--aurora-border-default`, `--aurora-accent-primary`, `--aurora-accent-pink`, `--aurora-accent-violet`.
- No raw GitHub UI cloning.
- No in-app explanatory prose about how the dashboard works.
- Cards use 8px radius for tables and 14-22px for panels.
- Status badges are compact square chips, not large saturated pills.
- Use tabular numerals for metrics.
- Keep the page operational and scan-friendly; avoid marketing hero sections.
- Show empty states for missing GitHub, Beads, or checks data.

## Self-check

- GitHub and Beads values each have source notes in provenance.
- No credentials or private metadata are written.
- The dashboard still works when Beads is unavailable.
- PR check/review labels are distinguishable without color alone.
- Beads queue cards identify ready, blocked, and stale work separately.
- The first viewport shows repository identity, KPI strip, PR health, and Beads queues.
