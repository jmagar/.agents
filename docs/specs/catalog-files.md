# Catalog Files Spec

Status: draft
Owner: local agent marketplace workshop
Applies to: `/home/jmagar/.agents/catalog`

## Purpose

Catalog files are the structured plugin inventory and generation instructions for marketplace output. They do not contain the reusable capability body. Capability bodies live in `shared/`; catalog files say which shared artifacts are included in a plugin, where that plugin is published, which platforms receive it, and how generation should render it.

Use this split:

- `shared/` is content: skill directories, prompts, hook scripts, command bodies, MCP fragments, themes, and reusable files.
- `catalog/` is plugin/package metadata: IDs, ownership, provenance, marketplace bucket, plugin membership, target platforms, source references, generation rules, publishability, and output mappings.

## File Layout

Catalog files start with plugin/package entries only:

```text
catalog/
  plugins/<plugin-id>.yaml
```

Catalog files are authored in YAML. File names must use stable kebab-case IDs and the `.yaml` extension. The filename stem should match the top-level `id` field.

Do not create `catalog/agents/`, `catalog/mcp/`, `catalog/hooks/`, or similar component catalogs unless a later design proves component-level metadata is necessary. For now, plugin catalog files reference component source directly under `shared/`.

## Common Fields

Every catalog file must include:

| Field | Meaning |
|---|---|
| `id` | Stable kebab-case ID matching the filename stem. |
| `kind` | Must be `plugin`. |
| `version` | Catalog metadata version for this entry. |
| `status` | `draft`, `active`, `deprecated`, or `retired`. |
| `owner` | Human or project owner. |
| `description` | Short human-readable purpose. |
| `source_refs` | Paths to canonical source content, usually under `shared/`. |
| `targets` | Platform targets: `claude`, `codex`. |
| `provenance` | Origin and trust metadata. |

Catalog paths must not point at `generated/` as source. Generated output is never canonical.

`catalog/plugins/<plugin-id>.yaml` defines package membership and publication routing.

Required plugin-specific fields:

| Field | Meaning |
|---|---|
| `bucket` | One of `curated-marketplace`, `flow-marketplace`, `vibe-marketplace`. |
| `plugin_root` | Bucket-local plugin payload path, normally `<bucket>/plugins/<plugin-id>`. |
| `marketplaces` | Marketplace targets and publish state for Claude/Codex output. |
| `components` | Shared source paths included in the plugin, grouped by component type. |
| `generation` | Render/copy rules and whether output is strict. |

Example:

```yaml
id: vibin
kind: plugin
version: 0.1.0
status: draft
owner: local
description: Local workflow plugin for session, GitHub, and CI helpers.
bucket: vibe-marketplace
plugin_root: vibe-marketplace/plugins/vibin
targets:
  - claude
  - codex
source_refs:
  - shared/skills/gh-address-comments
components:
  skills:
    - shared/skills/gh-address-comments
  hooks: []
  agents: []
  commands: []
marketplaces:
  claude:
    enabled: true
    publish_state: draft
  codex:
    enabled: true
    publish_state: draft
generation:
  strict: true
  copy_shared_sources: true
  allow_inline_content: false
provenance:
  origin: local
  upstream_url: null
  license: null
```

## Component References

Components are referenced by path, not by separate component catalog IDs.

Example:

```yaml
components:
  skills:
    - shared/skills/gh-address-comments
  agents:
    - shared/agents/rust-reviewer
  mcp:
    - shared/mcp/github.json
```

If a component needs platform-specific output settings, put those settings under the plugin's `platform` or `generation` block and reference the shared path there. Do not add a second catalog file just to describe one component.

## Strict Generation

`generation.strict` controls how closely a generated plugin must match the catalog.

- `true`: generated output must contain only catalog-declared components, source refs, and platform mappings. Missing source refs, undeclared components, or generated files outside declared outputs are validation errors.
- `false`: generated output may include extra platform scaffolding or compatibility files, but those files must be listed under `generation.allowed_extra_outputs` or clearly marked generated.

Use `strict: true` for publishable marketplace plugins. Use `strict: false` only for migration, compatibility packs, or exploratory generation.

## Inline Content

Catalog files should reference dedicated source files under `shared/`. Inline content is allowed only for tiny metadata-level snippets, not full skills, agents, hooks, command bodies, or themes.

Rules:

- Prefer `source_refs` to `inline`.
- Do not inline `SKILL.md` bodies.
- Do not inline long prompts.
- Do not inline hook scripts.
- Inline content must be copied into generated output deterministically and covered by validation.

## Validation Rules

A validator should:

1. Load `docs/contracts/catalog-files.contract.json`.
2. Verify every catalog file has required common fields.
3. Verify filename stem matches `id`.
4. Verify `kind` matches the catalog subdirectory.
5. Verify `source_refs` exist and do not point under `generated/`.
6. Verify plugin `bucket` and `plugin_root` stay inside the Claude/Codex marketplace structure.
7. Verify component paths referenced by `catalog/plugins/*.yaml` exist under `shared/`.
8. Verify target platform mappings only use supported platform/component pairs from the Claude/Codex marketplace contract.
9. Enforce `generation.strict` rules for generated output.
