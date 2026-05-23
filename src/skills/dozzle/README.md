# Dozzle

Lab's Dozzle integration — Real-time Docker container log viewer. Use when the user wants to manage their Dozzle instance, or invokes `lab dozzle` / `mcp__lab__dozzle`. Calls the MCP tool first, falls back to the CLI if MCP is unavailable.

## Usage

Invoke this skill when the user request matches the trigger conditions in `SKILL.md`. The skill body is the source of truth for workflow steps and operational constraints.

## Files

- `SKILL.md` - agent workflow and trigger guidance
- `agents/` - OpenAI runtime metadata
- `references/` - progressively loaded reference material
- `README.md` - packaging overview
- `CHANGELOG.md` - packaging change history
