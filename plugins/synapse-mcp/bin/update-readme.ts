#!/usr/bin/env tsx
// scripts/update-readme.ts
import { readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { getSchemaDescription } from "@modelcontextprotocol/sdk/server/zod-compat.js";
import { FLUX_SUBACTION_COUNT, FluxSchema } from "../src/schemas/flux/index.js";
import { SCOUT_SUBACTION_COUNT, ScoutSchema } from "../src/schemas/scout/index.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, "..");
const readmePath = join(rootDir, "README.md");

async function updateReadme(): Promise<void> {
  console.log("📖 Reading README.md...");
  const readme = await readFile(readmePath, "utf-8");

  // Extract top-level descriptions from schemas
  const fluxDesc = getSchemaDescription(FluxSchema) ?? "Docker infrastructure management";
  const scoutDesc = getSchemaDescription(ScoutSchema) ?? "SSH remote operations";

  console.log("✓ Flux description:", fluxDesc);
  console.log("✓ Scout description:", scoutDesc);

  let updated = readme;

  // Update the "Total: N subactions" count line in the flux section header
  const fluxCountRegex =
    /(### `flux` [^\n]*\n\nRoutes by `action`, then `subaction`\. Total: )\d+( subactions\.)/;
  if (fluxCountRegex.test(updated)) {
    updated = updated.replace(fluxCountRegex, `$1${FLUX_SUBACTION_COUNT}$2`);
    console.log("✓ Updated flux tool section");
  } else {
    console.warn("⚠️ Could not find flux tool section");
  }

  // Update the "Total: N operations" count line in the scout section header
  const scoutCountRegex = /(### `scout` [^\n]*\n\nRoutes by `action`\. Total: )\d+( operations\.)/;
  if (scoutCountRegex.test(updated)) {
    updated = updated.replace(scoutCountRegex, `$1${SCOUT_SUBACTION_COUNT}$2`);
    console.log("✓ Updated scout tool section");
  } else {
    console.warn("⚠️ Could not find scout tool section");
  }

  // Check if README needs updating
  if (updated === readme) {
    console.log("✓ README already up-to-date");
    return;
  }

  // Write updated README
  await writeFile(readmePath, updated, "utf-8");
  console.log("✅ README.md updated successfully");
}

updateReadme().catch((error) => {
  console.error("❌ Failed to update README:", error);
  process.exit(1);
});
