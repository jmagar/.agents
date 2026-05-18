# Claude/Codex Marketplace Repository Structure Spec

Status: draft
Owner: local agent marketplace workshop
Applies to: `/home/jmagar/.agents`

## Purpose

This repository is the source workspace for three marketplace buckets targeting Claude Code and Codex. The structure must minimize duplication, make marketplace boundaries obvious, and avoid treating Claude Code and Codex as if they have identical plugin models.

## Marketplace Buckets

The repo has three top-level marketplace buckets. These names are part of the contract.

| Bucket | Purpose | Trust/provenance boundary |
|---|---|---|
| `curated-marketplace/` | Favored third-party plugins, wrappers, mirrors, or compatibility packs. | External-origin content that is endorsed or adapted locally. |
| `flow-marketplace/` | Operating packs for upstream/self-hosted services. | Service-specific workflows, MCP configs, skills, hooks, and runbooks. |
| `vibe-marketplace/` | Original local projects and workflows. | Locally authored projects that do not depend on upstream plugin ownership. |

Each bucket is a marketplace root for Claude Code and Codex:

```text
<bucket>/
  .claude-plugin/
    marketplace.json
  .agents/
    plugins/
      marketplace.json
  plugins/
    <plugin-name>/
```

The marketplace files may be absent while the bucket is still being scaffolded, but the directories are reserved and must not be reused for other purposes. A bucket is considered publishable only when its Claude and Codex marketplace files exist and reference plugin payloads inside that bucket.

## Plugin Payload Layout

Each plugin payload under a marketplace bucket should follow this shape when it uses the relevant component:

```text
<bucket>/plugins/<plugin-name>/
  .claude-plugin/
    plugin.json
  .codex-plugin/
    plugin.json
  agents/
    claude/
    codex/
  commands/
    claude/
  hooks/
    claude/
    codex/
  skills/
  output-styles/
  channels/
  monitors/
  themes/
  mcp/
  lsp/
  bin/
  settings/
```

Not every plugin needs every directory. Component directories are allowed when the plugin ships or generates that component.

## Shared Source and Generated Output

Shared source is the canonical place for reusable component intent. Generated output is not source of truth.

```text
shared/
  agents/
  bin/
  channels/
  commands/
  hook-scripts/
  hooks/
  lsp/
  mcp/
  monitors/
  output-styles/
  prompts/
  scripts/
  settings/
  skills/
  themes/

catalog/
  plugins/

templates/
  plugin/

generated/
  claude/
  codex/
```

Rules:

- `shared/` stores the reusable source artifacts themselves: skill directories, agent prompts, hook scripts, MCP config fragments, command bodies, theme files, and other capability content that may be packaged for Claude, Codex, or both.
- `catalog/` stores structured package metadata: plugin membership, target platforms, bucket ownership, provenance, generation rules, publishability, and source-to-output mappings. Catalog files should reference `shared/` content by relative path; they should not duplicate the capability body.
- `templates/` stores skeletons and rendering templates.
- `generated/` stores generated artifacts only. Do not hand-edit generated files unless the generated contract explicitly allows it.
- `shared/skills/` is the canonical source location for local skills. Root `skills/` is not a canonical source location after migration.
- Root `plugins/` is legacy/scratch and is not part of the marketplace contract.

Use this rule of thumb:

- If a human edits the reusable capability itself, put it in `shared/`.
- If a human edits inventory, ownership, targets, provenance, package membership, or generator behavior, put it in `catalog/plugins/<plugin-id>.yaml`.

Example:

```text
shared/
  skills/
    gh-address-comments/
      SKILL.md

catalog/
  plugins/
    vibin.yaml
```

In that example, `shared/skills/gh-address-comments/` contains the real skill. `catalog/plugins/vibin.yaml` decides whether that skill is packaged into Claude, Codex, or both outputs. There is no separate `catalog/skills/gh-address-comments.yaml` unless reuse pressure proves that component-level metadata is needed.

## Component Semantics

| Component | Shared/source location | Platform packaging rule |
|---|---|---|
| Agents | `shared/agents/`, `shared/prompts/` | Generate per platform. Claude uses Markdown/frontmatter plugin agents. Codex uses standalone TOML and may need separate installation because Codex plugins do not currently provide a stable agent distribution surface. Plugin catalog files reference included agents by `shared/` path. |
| Commands | `shared/commands/` | Claude can package commands. Codex supports custom slash commands locally, but this repo does not assume a Codex plugin-distributed custom command surface. Plugin catalog files reference included commands by `shared/` path. |
| Hooks | `shared/hooks/`, `shared/hook-scripts/` | Claude plugins can package hooks. Codex hooks exist and plugin manifest support has been observed, but Codex runtime docs still emphasize config-layer discovery, so generators must model Codex hooks separately from Claude hooks. Plugin catalog files reference included hooks by `shared/` path. |
| Skills | `shared/skills/` | Skills are the most portable component and should be shared where possible. |
| Output styles | `shared/output-styles/` | Claude plugin surface. No Codex equivalent is assumed. |
| Channels | `shared/channels/` | Claude plugin surface. No Codex equivalent is assumed. |
| Monitors | `shared/monitors/` | Claude plugin surface. No Codex equivalent is assumed. |
| Themes | `shared/themes/` | Claude plugin surface. Codex theme support is not assumed. |
| MCP servers | `shared/mcp/` | Supported by Claude and Codex, but config file shape differs. Plugin catalog files reference included MCP config by `shared/` path. |
| LSP servers | `shared/lsp/` | Claude plugin surface. No Codex plugin equivalent is assumed. |
| `bin/` tools | `shared/bin/` | Claude adds plugin `bin/` to PATH. Codex can use scripts but no general equivalent PATH contract is assumed. |
| Plugin settings | `shared/settings/` | Claude plugins can ship `settings.json`. Codex settings are platform-specific and should be generated explicitly when needed. |

## Path Rules

- Marketplace plugin sources should resolve inside their bucket root, normally `./plugins/<plugin-name>`.
- Do not require marketplace files to reference `../shared` or other paths outside the bucket root.
- If a plugin needs shared files, copy, generate, or symlink them into the plugin payload as part of an explicit build step.
- Do not add new canonical skill source under root `skills/`; put migrated and new skills under `shared/skills/`.
- Do not treat root `plugins/` as marketplace payload without an explicit migration.

## Required Invariants

The repo structure must preserve these invariants:

1. The three marketplace bucket directories exist at repo root.
2. Each bucket contains `.claude-plugin/`, `.agents/plugins/`, and `plugins/`.
3. Shared component source directories exist for every supported component family.
4. Template plugin skeleton includes every known Claude/Codex plugin component directory.
5. Local skill source lives under `shared/skills/`; root `skills/` is not canonical after migration.
6. Root `plugins/` remains outside the contract unless explicitly migrated.

## Validation Strategy

A future validator should:

1. Load `docs/contracts/claude-codex-marketplace-repo-structure.contract.json`.
2. Verify required directories exist.
3. Treat marketplace files as phase-dependent: optional in `draft` scaffolds, required for `published` buckets.
4. Verify forbidden/invented files are absent.
5. Verify `_template/` skeletons include the full Claude/Codex component set.
6. Optionally verify generated files are up to date against `catalog/` and `shared/`.
