import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const pluginRootCandidates = [
  resolve(process.cwd(), "plugins/live-consultant"),
  resolve(process.cwd(), "../../plugins/live-consultant")
];
const pluginRoot = pluginRootCandidates.find((candidate) =>
  existsSync(resolve(candidate, "assets/skill-knowledge-manifest.json"))
);
assert.ok(pluginRoot, "could not locate the exported or private Live Consultant plugin tree");

const knowledge = await import("../lib/live-consultant-knowledge.js");
knowledge.resetKnowledgeCacheForTests();

test("catalog loads all declared skills without external services", async () => {
  const catalog = await knowledge.loadKnowledgeCatalog();
  assert.equal(catalog.skills.size, 24);
  const declaredFiles = new Set(
    [...catalog.skills.values()].flatMap((skill) => skill.files)
  );
  assert.equal(catalog.documents.size, declaredFiles.size);
  assert.ok(catalog.documents.size > 0);
  assert.match(catalog.digest, /^[0-9a-f]{64}$/);
});

test("hosted-first assembly is mandatory with complete local fallback", async () => {
  const protocol = await readFile(
    resolve(
      pluginRoot,
      "skills/founder-business-consultant/references/skill-assembly-protocol.md"
    ),
    "utf8"
  );
  assert.match(protocol, /route_consultation/);
  assert.match(protocol, /load_knowledge_bundle/);
  assert.match(protocol, /next_cursor`; the hosted load is complete when/);
  assert.match(protocol, /next_cursor` is `null`/);
  assert.match(protocol, /hosted tools are absent or unavailable, fall back/);
  assert.match(protocol, /restart\s+the hosted route and load from the first page/);
});

test("knowledge identity binds control-plane and deployment versions", async () => {
  const catalog = await knowledge.loadKnowledgeCatalog();
  const current = knowledge.computeKnowledgeIdentityDigest({
    manifest: catalog.manifest,
    routingFixtures: catalog.routingFixtures,
    pluginManifest: catalog.pluginManifest,
    releaseMarker: catalog.releaseMarker,
    documents: catalog.documents
  });
  assert.equal(current, catalog.digest);

  const changedPlugin = knowledge.computeKnowledgeIdentityDigest({
    manifest: catalog.manifest,
    routingFixtures: catalog.routingFixtures,
    pluginManifest: { ...catalog.pluginManifest, version: "999.0.0" },
    releaseMarker: catalog.releaseMarker,
    documents: catalog.documents
  });
  assert.notEqual(changedPlugin, current);

  const changedRouting = knowledge.computeKnowledgeIdentityDigest({
    manifest: catalog.manifest,
    routingFixtures: {
      ...catalog.routingFixtures,
      schema_version: `${catalog.routingFixtures.schema_version}-changed`
    },
    pluginManifest: catalog.pluginManifest,
    releaseMarker: catalog.releaseMarker,
    documents: catalog.documents
  });
  assert.notEqual(changedRouting, current);

  const changedRuntime = knowledge.computeKnowledgeIdentityDigest({
    manifest: catalog.manifest,
    routingFixtures: catalog.routingFixtures,
    pluginManifest: catalog.pluginManifest,
    releaseMarker: catalog.releaseMarker,
    documents: catalog.documents,
    runtimeSchemaVersion: "999.0.0"
  });
  assert.notEqual(changedRuntime, current);
});

test("every routing fixture selects its complete required skill stack", async () => {
  const catalog = await knowledge.loadKnowledgeCatalog();
  for (const fixture of catalog.routingFixtures.fixtures) {
    const route = await knowledge.routeConsultation({ query: fixture.prompt_summary });
    const selected = new Set(route.selected_skills.map((skill) => skill.skill_id));
    for (const skillId of fixture.required_skills) {
      assert.ok(selected.has(skillId), `${fixture.id} omitted ${skillId}`);
    }
  }
});

test("bundle pagination reconstructs every selected file exactly once", async () => {
  const catalog = await knowledge.loadKnowledgeCatalog();
  const skillIds = ["audit-business", "reason-business-decision"];
  const expectedPaths = new Set(skillIds.flatMap((skillId) => catalog.skills.get(skillId).files));
  const reconstructed = new Map();
  let cursor;
  let pages = 0;
  do {
    const page = await knowledge.loadKnowledgeBundle({
      skill_ids: skillIds,
      cursor,
      page_size_chars: 2_000
    });
    pages += 1;
    for (const chunk of page.chunks) {
      const current = reconstructed.get(chunk.path) ?? "";
      assert.equal(current.length, chunk.start_character);
      reconstructed.set(chunk.path, current + chunk.content);
    }
    cursor = page.next_cursor ?? undefined;
    if (!cursor) assert.equal(page.complete, true);
  } while (cursor);

  assert.ok(pages > 1);
  assert.deepEqual(new Set(reconstructed.keys()), expectedPaths);
  for (const [path, content] of reconstructed) {
    assert.equal(content, catalog.documents.get(path), `content drifted for ${path}`);
  }
});

test("bundle cursors fail closed when tampered", async () => {
  const first = await knowledge.loadKnowledgeBundle({
    skill_ids: ["sell-like-crazy"],
    page_size_chars: 2_000
  });
  assert.ok(first.next_cursor);
  const decoded = JSON.parse(Buffer.from(first.next_cursor, "base64url").toString("utf8"));
  decoded.offset += 1;
  const tampered = Buffer.from(JSON.stringify(decoded)).toString("base64url");
  await assert.rejects(
    knowledge.loadKnowledgeBundle({
      skill_ids: ["sell-like-crazy"],
      cursor: tampered,
      page_size_chars: 2_000
    }),
    /cursor/
  );
});

test("bundle cursors reject a valid cursor from another deployment identity", async () => {
  const first = await knowledge.loadKnowledgeBundle({
    skill_ids: ["sell-like-crazy"],
    page_size_chars: 2_000
  });
  const old = JSON.parse(Buffer.from(first.next_cursor, "base64url").toString("utf8"));
  old.digest = "0".repeat(64);
  old.checksum = createHash("sha256")
    .update(old.digest)
    .update("\0")
    .update(JSON.stringify(old.skill_ids))
    .update("\0")
    .update(String(old.offset))
    .digest("hex");
  const oldCursor = Buffer.from(JSON.stringify(old)).toString("base64url");
  await assert.rejects(
    knowledge.loadKnowledgeBundle({
      skill_ids: ["sell-like-crazy"],
      cursor: oldCursor,
      page_size_chars: 2_000
    }),
    /knowledge version/
  );
});

function parseRpcPayload(text) {
  if (text.trim().startsWith("{")) return JSON.parse(text);
  const data = text
    .split(/\r?\n/)
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trim())
    .filter(Boolean)
    .at(-1);
  if (!data) throw new Error(`No MCP payload in response: ${text}`);
  return JSON.parse(data);
}

async function rpc(handler, body) {
  const response = await handler(
    new Request("http://localhost/mcp", {
      method: "POST",
      headers: {
        accept: "application/json, text/event-stream",
        "content-type": "application/json"
      },
      body: JSON.stringify(body)
    })
  );
  assert.equal(response.status, 200);
  return parseRpcPayload(await response.text());
}

test("Streamable HTTP exposes the three stable read-only tools", async () => {
  const { POST } = await import("../app/[transport]/route.js");
  const initialize = await rpc(POST, {
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: {
      protocolVersion: "2025-03-26",
      capabilities: {},
      clientInfo: { name: "offline-contract-test", version: "1.0.0" }
    }
  });
  assert.equal(initialize.result.serverInfo.name, "live-consultant");

  const list = await rpc(POST, { jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });
  assert.deepEqual(
    list.result.tools.map((tool) => tool.name).sort(),
    ["live_consultant_status", "load_knowledge_bundle", "route_consultation"]
  );
  const schemas = Object.fromEntries(
    list.result.tools.map((tool) => [tool.name, tool.inputSchema])
  );
  assert.deepEqual(schemas, {
    route_consultation: {
      type: "object",
      properties: {
        query: {
          type: "string",
          minLength: 1,
          maxLength: 12_000,
          description: "The specific business decision or deliverable requested."
        },
        business_context: {
          type: "string",
          maxLength: 4_000,
          description: "Only task-specific business facts needed for routing, such as niche, buyer, offer, stage, geography, channel, and constraints. Do not send conversation history, raw transcripts, credentials, personal data, customer lists, or regulated data."
        }
      },
      required: ["query"],
      additionalProperties: false,
      $schema: "http://json-schema.org/draft-07/schema#"
    },
    load_knowledge_bundle: {
      type: "object",
      properties: {
        skill_ids: {
          type: "array",
          items: { type: "string" },
          minItems: 1,
          maxItems: 24
        },
        cursor: { type: "string" },
        page_size_chars: { type: "integer", minimum: 2_000, maximum: 30_000 }
      },
      required: ["skill_ids"],
      additionalProperties: false,
      $schema: "http://json-schema.org/draft-07/schema#"
    },
    live_consultant_status: {
      $schema: "http://json-schema.org/draft-07/schema#",
      type: "object",
      properties: {}
    }
  });
  for (const tool of list.result.tools) {
    assert.equal(tool.outputSchema.type, "object");
    assert.equal(tool.outputSchema.additionalProperties, false);
    assert.equal(tool.annotations.readOnlyHint, true);
    assert.equal(tool.annotations.destructiveHint, false);
  }

  const call = await rpc(POST, {
    jsonrpc: "2.0",
    id: 3,
    method: "tools/call",
    params: { name: "live_consultant_status", arguments: {} }
  });
  assert.equal(call.result.structuredContent.service, "live-consultant");
  assert.equal(call.result.structuredContent.persistence, "none");
  assert.equal(call.result.structuredContent.external_fetching, false);

  const routeCall = await rpc(POST, {
    jsonrpc: "2.0",
    id: 4,
    method: "tools/call",
    params: {
      name: "route_consultation",
      arguments: {
        query: "Audit lead generation for a Toronto HVAC business",
        business_context: "Local service business selling to homeowners"
      }
    }
  });
  assert.equal(routeCall.result.isError, undefined);
  assert.ok(routeCall.result.structuredContent.selected_skills.length > 0);

  const bundleCall = await rpc(POST, {
    jsonrpc: "2.0",
    id: 5,
    method: "tools/call",
    params: {
      name: "load_knowledge_bundle",
      arguments: {
        skill_ids: ["sell-like-crazy"],
        page_size_chars: 2_000
      }
    }
  });
  assert.equal(bundleCall.result.isError, undefined);
  assert.equal(bundleCall.result.structuredContent.selected_skill_ids[0], "sell-like-crazy");
  assert.ok(bundleCall.result.structuredContent.chunks.length > 0);
});

test("health and OpenAI domain challenge routes reveal no secrets", async () => {
  const health = await import("../app/healthz/route.js");
  const healthResponse = await health.GET();
  assert.equal(healthResponse.status, 200);
  const healthBody = await healthResponse.json();
  assert.equal(healthBody.ok, true);
  assert.equal(healthBody.prompt_logging, false);

  const challengeRoute = await import("../app/.well-known/openai-apps-challenge/route.js");
  delete process.env.OPENAI_APPS_CHALLENGE;
  assert.equal((await challengeRoute.GET()).status, 503);
  process.env.OPENAI_APPS_CHALLENGE = "test-domain-challenge";
  const challengeResponse = await challengeRoute.GET();
  assert.equal(challengeResponse.status, 200);
  assert.equal(await challengeResponse.text(), "test-domain-challenge");
  delete process.env.OPENAI_APPS_CHALLENGE;
});
