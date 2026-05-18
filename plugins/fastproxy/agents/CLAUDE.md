# `agents/`

Project-level agent definitions for fastproxy.

Each `.md` file is a Claude Code subagent with YAML frontmatter (`name`, `description`, `tools`).

## Agents

- `fastproxy-admin.md` — manages upstream servers, user blocklists, and proxy health

## Adding Agents

Create a new `.md` file with frontmatter:

```markdown
---
name: agent-name
description: |
  When to use this agent and what it does.
tools: Read, Write, Bash, Glob, Grep
---

# Agent Name

Agent instructions here.
```
