# Bitwarden

Use whenever the user mentions Bitwarden — vault items, logins, passwords, secure notes, cards, identities, folders, collections, attachments, Sends, organizations (members, groups, policies, collections, events, subscription, device approvals), password/passphrase generation, vault sync/lock/unlock, BW_SESSION handling, the Bitwarden CLI (`bw`), or the Bitwarden MCP server. Prefer the MCP tools (`mcp__bitwarden__*`) over shelling out to `bw`; only fall back to the CLI for session lifecycle (unlock/lock/status) and operations the MCP server does not expose.

## Usage

Invoke this skill when the user request matches the trigger conditions in `SKILL.md`. The skill body is the source of truth for workflow steps and operational constraints.

## Files

- `SKILL.md` - agent workflow and trigger guidance
- `agents/` - OpenAI runtime metadata
- `scripts/` - helper scripts
- `README.md` - packaging overview
- `CHANGELOG.md` - packaging change history
