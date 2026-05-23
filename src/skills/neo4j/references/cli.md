# Neo4J CLI Reference

Use the CLI only when the MCP tool is unavailable or the user explicitly asks for shell commands.

## Discovery

```bash
lab neo4j --help
lab neo4j <action> --help
labby --json neo4j <action> ...
```

MCP action names with dots are exposed as dash-separated CLI commands, for example `server.health` becomes `server-health`.

Prefer JSON output where available so results can be parsed instead of scraped.
