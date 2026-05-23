# UniFi Skill (rustifi)

Use this skill whenever the user asks about their UniFi network — connected clients, who's on the WiFi, which devices are online, access points, switches, gateways, network health, site health, active alarms, network events, WiFi configurations (SSIDs), controller sysinfo, or their authenticated UniFi identity. This skill covers the rustifi MCP server (read-only Rust bridge to the UniFi REST API via X-API-KEY). Trigger phrases include: "UniFi clients", "connected clients", "who's on the network", "UniFi devices", "access points", "APs", "UniFi switches", "WiFi networks", "WLAN config", "SSIDs", "network health", "UniFi health", "site health", "UniFi alarms", "network alerts", "network events", "UniFi events", "sysinfo", "controller version", "UniFi me". Always use this skill rather than guessing at curl commands or API paths — the UniFi REST API has several gotchas around path prefixes and auth that this skill encodes.

## Usage

Invoke this skill when the user request matches the trigger conditions in `SKILL.md`. The skill body is the source of truth for workflow steps and operational constraints.

## Files

- `SKILL.md` - agent workflow and trigger guidance
- `agents/` - OpenAI runtime metadata
- `README.md` - packaging overview
- `CHANGELOG.md` - packaging change history
