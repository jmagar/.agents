---
date: 2026-05-24 17:14:24 EST
repo: https://github.com/jmagar/.agents.git
branch: main
head: bb4fda7
working directory: /home/jmagar/.agents
worktree: /home/jmagar/.agents
beads: agents-rxf, agents-2nt
---

# Dozzle MCP, Lab Gateway, And mcporter Setup

## User Request

The session started with fixing the Dozzle skill after stale Lab/cookie guidance caused confusion, then expanded into enabling Dozzle's native MCP endpoint, adding it to Lab, and adding it to mcporter.

## Session Overview

- Corrected the Dozzle workflow distinction between direct Dozzle API use, Dozzle native MCP, Lab gateway upstreams, Claude plugin `.mcp.json`, and mcporter config.
- Enabled Dozzle MCP on the runtime host and verified `/api/mcp` exposes Dozzle MCP tools.
- Added Dozzle to Lab gateway config and reloaded the gateway.
- Added Dozzle to mcporter's system config and verified tool discovery plus read-only calls.

## Sequence of Events

1. Reviewed and corrected the Dozzle skill so it no longer points users at stale `lab dozzle` or fake Lab MCP paths for direct API work.
2. Used Dozzle docs/repo evidence and Axon-backed checks earlier in the session to validate auth, Authelia/forward-proxy, Tailnet boundary, and MCP behavior.
3. Added native Dozzle MCP plugin config in the Lab repo and configured the Claude plugin user setting to `https://dozzle.tootie.tv/api/mcp`.
4. Checked `squirts:/mnt/compose/dozzle`, added `DOZZLE_ENABLE_MCP=true`, recreated the Dozzle container, and verified `/api/mcp`.
5. Added Dozzle as a Lab gateway upstream in `~/.lab/config.toml`, tested it, and reloaded Lab gateway metadata.
6. Added Dozzle to mcporter system config and verified discovery and read-only calls.

## Key Findings

- Dozzle was not a Lab built-in service and should not be treated as `lab dozzle`; direct Dozzle API checks and native Dozzle MCP are separate surfaces.
- Dozzle's native MCP endpoint is `https://dozzle.tootie.tv/api/mcp`.
- Runtime MCP required `DOZZLE_ENABLE_MCP=true` in the Dozzle compose environment.
- Lab gateway now sees Dozzle as a custom HTTP MCP upstream with four exposed tools.
- mcporter's `config add` help advertised `--scope` and `--persist`, but those flags parsed as server names in this environment, so the system config was edited directly.

## Technical Decisions

- Used Dozzle's native MCP endpoint instead of inventing a Lab service shim because Dozzle already exposes the required MCP tools.
- Kept Dozzle direct API guidance in the skill separate from Lab gateway guidance to avoid routing simple operational probes through the wrong control plane.
- Added mcporter configuration to `/home/jmagar/.mcporter/mcporter.json`, not repo-local `.agents/config/mcporter.json`, because existing mcporter servers are loaded from the system config.
- Cleaned up the accidental repo-local `config/` directory after mcporter misparsed `--scope`/`--persist`.

## Files Changed

| status | path | previous path | purpose | evidence |
|---|---|---|---|---|
| modified | `/home/jmagar/workspace/lab/plugins/dozzle/.mcp.json` | | Added Claude plugin MCP server entry for Dozzle | `rg` found `dozzle` entry |
| modified | `/home/jmagar/workspace/lab/plugins/dozzle/.claude-plugin/plugin.json` | | Added `mcpServers` and `userConfig.dozzle_mcp_url` | committed in Lab repo |
| modified | `/home/jmagar/workspace/lab/plugins/dozzle/skills/dozzle/SKILL.md` | | Corrected stale Dozzle routing/auth guidance | committed in Lab repo |
| modified | `/home/jmagar/.lab/config.toml` | | Added Lab gateway upstream named `dozzle` | lines 260-262 show name and URL |
| modified | `/home/jmagar/.mcporter/mcporter.json` | | Added mcporter server `dozzle` | lines 73-74 show base URL |
| modified | `squirts:/mnt/compose/dozzle/docker-compose.yml` | | Enabled native Dozzle MCP | `docker inspect dozzle` showed `DOZZLE_ENABLE_MCP=true` earlier in the session |
| created | `docs/sessions/2026-05-24-dozzle-mcp-lab-mcporter.md` | | Session note | this file |

## Beads Activity

- `agents-rxf` — closed before this save; covered the stale Dozzle skill auth fallback guidance and direct API correction.
- `agents-2nt` — closed before this save; covered enhancing Dozzle auth/MCP guidance using Axon-grounded evidence.
- No new bead was created during the final save pass because no unfinished `.agents` repo task remained. The remaining Codex-session auth issue for `mcp__lab__.scout` was documented under Open Questions.

## Repository Maintenance

- Plans: checked `docs/plans/`; no plan files were present, so nothing was moved to `docs/plans/complete/`.
- Beads: read recent `.agents` beads and interactions. Relevant Dozzle beads were already closed; no tracker mutation was needed.
- Worktrees and branches: checked `.agents` worktrees and branches. Only `/home/jmagar/.agents` on `main` exists; local `main` matches `origin/main` at `bb4fda7`.
- Stale docs: the active stale-doc work for Dozzle had already been handled in the Lab repo commits `34e393e1` and `f97cf13a`; no additional `.agents` docs contradicted the current state.
- Cleanup: removed accidental `/home/jmagar/.agents/config/` after mcporter's broken flag parsing created a bogus repo-local project config. Final `.agents` status was clean before writing this note.

## Tools And Skills Used

- Skills: `dozzle`, `lab:using-lab-cli`, `mcporter`, `lavra:agent-browser`, `save-to-md`, plus earlier skill-creation/review workflows for the Dozzle skill updates.
- Shell commands: used `rg`, `sed`, `git`, `jq`, `mcporter`, `lab gateway`, `docker compose`, `docker inspect`, `curl`, `ssh`, `claude plugin`, and `bd`.
- MCP/tools: used Lab gateway CLI checks and attempted Codex's `mcp__lab__.scout`; that connector returned `Auth required`.
- Browser: used `agent-browser` against `https://dozzle.tootie.tv/api/mcp`; endpoint loaded as expected for a protocol route with no interactive UI.
- File tools: used patch edits for repo and config changes; used shell reads for verification.

## Commands Executed

```bash
lab gateway add --name dozzle --url https://dozzle.tootie.tv/api/mcp --json
LAB_LOG=error lab gateway test --name dozzle --json
LAB_LOG=error lab gateway reload --json
LAB_LOG=error lab gateway get dozzle --json
mcporter list dozzle --schema --json
mcporter call dozzle.list_hosts --output text
mcporter call dozzle.list_containers state=running --output text
mcporter call dozzle.get_container_logs host=ae80236a-32f1-4846-a40f-937782cfaea1 container_id=034681d5d1fd since_minutes=1 stream=all --output text
mcporter config doctor
```

## Errors Encountered

- `mcp__lab__.scout` failed with `Auth required`; Lab gateway CLI verification was used instead.
- `mcporter config add --scope home ...` and `mcporter config add --persist ...` misparsed flags as server names. The bogus entries were removed and `/home/jmagar/.mcporter/mcporter.json` was edited directly.
- Parsing the full `list_containers` output through `jq` failed because command output was too large/truncated. A targeted `rg` search found the Dozzle container ID, then logs/stats calls were made against that ID.
- `get_container_stats` with `container_id=dozzle` returned `container not found`; using the actual container ID `034681d5d1fd` succeeded.

## Behavior Changes

| Before | After |
|---|---|
| Dozzle skill mixed stale Lab/cookie guidance with real Dozzle behavior. | Dozzle skill now separates direct API, auth boundary, and MCP guidance. |
| Dozzle runtime did not expose native MCP at `/api/mcp`. | Dozzle runtime has `DOZZLE_ENABLE_MCP=true` and exposes native MCP. |
| Lab gateway had no Dozzle upstream. | Lab gateway has enabled upstream `dozzle` targeting `https://dozzle.tootie.tv/api/mcp`. |
| mcporter did not know about Dozzle. | mcporter can list and call Dozzle MCP tools by `dozzle.*` selectors. |

## Verification Evidence

| command | expected | actual | status |
|---|---|---|---|
| `lab gateway test --name dozzle --json` | Dozzle connects through Lab | `tool_count: 4`, `last_error: null` | pass |
| `lab gateway list --json` | Dozzle listed and connected | `dozzle connected=true tools=4/4 target=https://dozzle.tootie.tv/api/mcp` | pass |
| `lab gateway reload --json` | Gateway surfaces reload | `tools_changed`, `resources_changed`, and `prompts_changed` true | pass |
| `mcporter list dozzle --schema --json` | Dozzle tools discovered | `ok get_container_logs,get_container_stats,list_containers,list_hosts` | pass |
| `mcporter call dozzle.list_hosts --output text` | Hosts returned | TOOTIE, SHART, SQUIRTS available | pass |
| `mcporter call dozzle.get_container_logs ...` | Log data returned | Dozzle log JSON returned | pass |
| `mcporter config doctor` | Config valid | `Config looks good.` | pass |

## Risks And Rollback

- Dozzle MCP exposes Docker/container observability over the configured route. Roll back by removing `DOZZLE_ENABLE_MCP=true` from the Dozzle compose file and recreating the container.
- Lab gateway rollback: remove the `[[upstream]] name = "dozzle"` block from `/home/jmagar/.lab/config.toml` and run `lab gateway reload --json`.
- mcporter rollback: remove the `"dozzle"` object from `/home/jmagar/.mcporter/mcporter.json`.
- Claude plugin rollback: uninstall or reconfigure `dozzle@jmagar-lab`, or remove `dozzle_mcp_url` from `~/.claude/settings.json`.

## Decisions Not Taken

- Did not build a new Lab-native Dozzle service, because Dozzle's native MCP server already exposes the needed tools.
- Did not add bearer auth to mcporter's Dozzle entry, because the endpoint worked without it from this environment and is already behind the user's network/proxy boundary assumptions.
- Did not create a new bead during save, because there was no confirmed unfinished repo work beyond the existing Codex-session Lab MCP auth issue.

## References

- Dozzle MCP endpoint: `https://dozzle.tootie.tv/api/mcp`
- Lab repo commits observed: `34e393e1 Add Dozzle skill drift guard`, `f97cf13a Add Dozzle native MCP config`
- Runtime compose location checked earlier: `squirts:/mnt/compose/dozzle`

## Open Questions

- Codex's active `mcp__lab__.scout` connector returned `Auth required`; Lab gateway CLI works, but the Codex connector auth state may still need repair if this session should use it directly.
- mcporter's `config add` help and parser behavior disagree for `--scope` and `--persist`; this should be investigated before relying on those flags in scripts.

## Next Steps

- Use `mcporter call dozzle.list_hosts --output text` or `mcporter call dozzle.list_containers state=running --output text` for future Dozzle MCP smoke checks.
- Use `lab gateway test --name dozzle --json` after Dozzle or Lab restarts to verify the Lab upstream remains healthy.
- If Codex needs Lab MCP access again, fix the `Auth required` condition on the `mcp__lab__` connector separately.
