#!/usr/bin/env npx tsx
// bin/smoke-test.ts
// Usage: SMOKE_URL=http://localhost:3000 AUTH_TOKEN=xxx npx tsx bin/smoke-test.ts

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const url = process.env.SMOKE_URL ?? "http://localhost:3000";
const token = process.env.AUTH_TOKEN;

if (!token) {
  console.error("AUTH_TOKEN env var required");
  process.exit(1);
}

const client = new Client({ name: "smoke-test", version: "1.0.0" });
const transport = new StreamableHTTPClientTransport(new URL(`${url}/mcp`), {
  requestInit: { headers: { Authorization: `Bearer ${token}` } },
});

try {
  await client.connect(transport);
  console.log("Connected to MCP server");

  // List tools
  const tools = await client.listTools();
  const arcaneTool = tools.tools.find((t) => t.name === "arcane");
  if (!arcaneTool) throw new Error("arcane tool not found");
  console.log(`arcane tool registered (${tools.tools.length} total)`);

  // List resources
  const resources = await client.listResources();
  console.log(`${resources.resources.length} resources registered`);

  // Call arcane:environment:list
  const result = await client.callTool({
    name: "arcane",
    arguments: { action: "environment", subaction: "list" },
  });
  console.log(
    "environment:list ->",
    result.content[0]?.type === "text"
      ? "got text response"
      : "unexpected response type",
  );

  // Test destructive gate
  const gateResult = await client.callTool({
    name: "arcane",
    arguments: {
      action: "container",
      subaction: "stop",
      envId: "test",
      id: "test",
    },
  });
  const gateText = (gateResult.content[0] as { text: string }).text;
  if (!gateText.includes("confirm: true"))
    throw new Error("Destructive gate not working");
  console.log("Destructive gate working");

  // Test new action enum values accepted by schema
  const systemResult = await client.callTool({
    name: "arcane",
    arguments: { action: "system", subaction: "docker-info", envId: "test" },
  });
  console.log(
    "system:docker-info ->",
    systemResult.content[0]?.type === "text" ? "schema accepted" : "unexpected",
  );

  const imageUpdateResult = await client.callTool({
    name: "arcane",
    arguments: { action: "image-update", subaction: "summary", envId: "test" },
  });
  console.log(
    "image-update:summary ->",
    imageUpdateResult.content[0]?.type === "text"
      ? "schema accepted"
      : "unexpected",
  );

  const vulnResult = await client.callTool({
    name: "arcane",
    arguments: { action: "vulnerability", subaction: "summary", envId: "test" },
  });
  console.log(
    "vulnerability:summary ->",
    vulnResult.content[0]?.type === "text" ? "schema accepted" : "unexpected",
  );

  const registryResult = await client.callTool({
    name: "arcane",
    arguments: { action: "registry", subaction: "list" },
  });
  console.log(
    "registry:list ->",
    registryResult.content[0]?.type === "text"
      ? "schema accepted"
      : "unexpected",
  );

  // Test new destructive gates
  const restoreGate = await client.callTool({
    name: "arcane",
    arguments: {
      action: "volume",
      subaction: "restore",
      envId: "test",
      id: "test-vol",
      params: { backupId: "bk-1" },
    },
  });
  const restoreText = (restoreGate.content[0] as { text: string }).text;
  if (!restoreText.includes("confirm: true"))
    throw new Error("volume:restore gate not working");
  console.log("volume:restore gate working");

  const syncGate = await client.callTool({
    name: "arcane",
    arguments: {
      action: "gitops",
      subaction: "sync",
      envId: "test",
      id: "sync-1",
    },
  });
  const syncText = (syncGate.content[0] as { text: string }).text;
  if (!syncText.includes("confirm: true"))
    throw new Error("gitops:sync gate not working");
  console.log("gitops:sync gate working");

  await client.close();
  console.log("\nAll smoke tests passed");
} catch (err) {
  console.error("Smoke test failed:", err);
  process.exit(1);
}
