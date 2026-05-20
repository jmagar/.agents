# GitHub + Beads Dashboard References

This reference set defines a reusable dashboard artifact for combining GitHub repository health with local Beads issue state.

## Files

- `template.html` — live-artifact-compatible HTML template with Aurora-style tokens.
- `example-data.json` — normalized example input data.
- `artifact-example.json` — minimal artifact creation metadata.
- `provenance-example.json` — example source notes and fallback tracking.

## Data Sources

Prefer `gh` for GitHub data and `bd` for Beads data.

Useful GitHub commands:

```bash
gh repo view OWNER/REPO --json nameWithOwner,description,url,primaryLanguage,licenseInfo,updatedAt,stargazerCount,forkCount,watchers
gh pr list --repo OWNER/REPO --state open --json number,title,author,updatedAt,labels,isDraft,reviewDecision,statusCheckRollup
gh issue list --repo OWNER/REPO --state open --json number,title,author,updatedAt,labels,assignees
```

Useful Beads commands:

```bash
bd status
bd ready --json
bd list --json
bd blocked --json
bd stale --json
bd stats --json
```

If a `bd` JSON command is not supported, use the plain-text command and record the fallback in `provenance.json`.
