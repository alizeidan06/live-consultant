import assert from "node:assert/strict";
import { createHash, createHmac } from "node:crypto";
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
const runtime = await import("../lib/live-consultant-runtime.js");
const TEST_RUNTIME_SECRET = "live-consultant-test-only-hmac-secret-2026-07-21";
knowledge.resetKnowledgeCacheForTests();
runtime.resetRuntimeCacheForTests();
runtime.registerRuntimeTokenSecretForTests(TEST_RUNTIME_SECRET);

const legacyToolContract = JSON.parse(
  await readFile(resolve(process.cwd(), "tests/fixtures/tool-contract.v0.5.1.json"), "utf8")
);
const currentToolContract = JSON.parse(
  await readFile(resolve(process.cwd(), "tests/fixtures/tool-contract.v0.6.0.json"), "utf8")
);

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function contractHash(value) {
  return createHash("sha256").update(canonicalJson(value)).digest("hex");
}

function testTokenMac(domain, payload) {
  return createHmac("sha256", TEST_RUNTIME_SECRET)
    .update(domain)
    .update("\0")
    .update(canonicalJson(payload))
    .digest("hex");
}

test("catalog loads all declared skills without external services", async () => {
  const catalog = await knowledge.loadKnowledgeCatalog();
  assert.equal(catalog.skills.size, 26);
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
  assert.match(protocol, /start_live_consultation/);
  assert.match(protocol, /load_live_consultant_bundle/);
  assert.match(protocol, /next_cursor`; the hosted load is complete when/);
  assert.match(protocol, /next_cursor` is `null`/);
  assert.match(protocol, /hosted tools are absent, unavailable, or\s+fail closed, fall back/);
  assert.match(protocol, /restart with `start_live_consultation`/);
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

test("new domain skills close over mandatory companions without expanding likely companions", async () => {
  const inventory = await knowledge.routeConsultation({
    query: "Our imported stock is aging, landed costs are unclear, and we need a 13-week cash plan."
  });
  const inventoryIds = new Set(inventory.selected_skills.map((skill) => skill.skill_id));
  for (const skillId of [
    "optimize-inventory-cash-flow",
    "audit-business",
    "reason-business-decision",
    "build-business-operations",
    "founder-business-consultant"
  ]) {
    assert.ok(inventoryIds.has(skillId), `inventory route omitted ${skillId}`);
  }
  assert.ok(!inventoryIds.has("plan-meta-ads"), "likely companions must not expand blindly");

  const meeting = await knowledge.routeConsultation({
    query: "Turn these messy business meeting notes and an unreliable speaker map into decisions and owners."
  });
  const meetingIds = new Set(meeting.selected_skills.map((skill) => skill.skill_id));
  for (const skillId of [
    "analyze-business-meeting",
    "audit-business",
    "reason-business-decision",
    "founder-business-consultant"
  ]) {
    assert.ok(meetingIds.has(skillId), `meeting route omitted ${skillId}`);
  }
  assert.ok(!meetingIds.has("plan-meta-ads"), "meeting routing must remain issue-driven");
  assert.ok(!meetingIds.has("founder-playbook-blue-ocean"), "generic meeting strategy must not imply category redesign");
  assert.ok(!meetingIds.has("founder-playbook-traction"), "generic meeting actions must not imply channel selection");

  const minimalMeeting = await knowledge.routeConsultation({
    query: "Analyze this meeting transcript."
  });
  const minimalMeetingIds = new Set(
    minimalMeeting.selected_skills.map((skill) => skill.skill_id)
  );
  for (const skillId of [
    "analyze-business-meeting",
    "audit-business",
    "reason-business-decision",
    "founder-business-consultant"
  ]) {
    assert.ok(minimalMeetingIds.has(skillId), `minimal meeting route omitted ${skillId}`);
  }
});

test("plain-language domain anchors improve recall without contaminating unrelated cash-flow work", async () => {
  for (const query of [
    "We have too much stock and no cash.",
    "Our warehouse inventory is not selling.",
    "Our shelves are full and the bank account is empty. What do we do?",
    "We keep buying products faster than customers buy them and now we cannot pay suppliers."
  ]) {
    const route = await knowledge.routeConsultation({ query });
    const selected = new Set(route.selected_skills.map((skill) => skill.skill_id));
    assert.ok(selected.has("optimize-inventory-cash-flow"), `inventory route missed: ${query}`);
  }

  for (const query of [
    "Turn this call into next steps.",
    "I have messy notes with four people arguing and no clear decision."
  ]) {
    const route = await knowledge.routeConsultation({ query });
    const selected = new Set(route.selected_skills.map((skill) => skill.skill_id));
    assert.ok(selected.has("analyze-business-meeting"), `meeting route missed: ${query}`);
  }

  for (const query of [
    "Help my consulting agency improve cash flow.",
    "Write a Sabri-style long-form homepage for my consulting agency that improves cash flow.",
    "Analyze our weekly cash flow for a no-inventory SaaS business."
  ]) {
    const route = await knowledge.routeConsultation({ query });
    const selected = new Set(route.selected_skills.map((skill) => skill.skill_id));
    assert.ok(!selected.has("optimize-inventory-cash-flow"), `false inventory route: ${query}`);
    assert.ok(!selected.has("analyze-business-meeting"), `false meeting route: ${query}`);
  }
});

test("a meeting-derived inventory problem selects the complete combined stack", async () => {
  const route = await knowledge.routeConsultation({
    query: "Review an importer meeting about urgent cash, slow stock, verbal product demand, channel choices, price, and automation before reliable data."
  });
  const selected = new Set(route.selected_skills.map((skill) => skill.skill_id));
  for (const skillId of [
    "analyze-business-meeting",
    "optimize-inventory-cash-flow",
    "founder-business-consultant",
    "audit-business",
    "reason-business-decision",
    "build-business-operations",
    "founder-playbook-mom-test",
    "validate-business-idea",
    "founder-playbook-monetizing-innovation"
  ]) {
    assert.ok(selected.has(skillId), `combined route omitted ${skillId}`);
  }
});

test("the shared anonymized inventory meeting case is deduplicated and associated with both skills", async () => {
  const sharedPath = "skills/analyze-business-meeting/references/cases.md";
  const seenPaths = new Set();
  let sharedContent = "";
  let cursor;
  do {
    const page = await knowledge.loadKnowledgeBundle({
      skill_ids: ["analyze-business-meeting", "optimize-inventory-cash-flow"],
      cursor,
      page_size_chars: 2_000
    });
    for (const chunk of page.chunks) {
      seenPaths.add(chunk.path);
      if (chunk.path === sharedPath) {
        assert.deepEqual(chunk.skill_ids, [
          "analyze-business-meeting",
          "optimize-inventory-cash-flow"
        ]);
        assert.equal(sharedContent.length, chunk.start_character);
        sharedContent += chunk.content;
      }
    }
    cursor = page.next_cursor ?? undefined;
  } while (cursor);
  assert.ok(seenPaths.has(sharedPath));
  assert.equal(sharedContent, (await knowledge.loadKnowledgeCatalog()).documents.get(sharedPath));
});

test("new meeting and inventory packs contain only sanitized portable synthesis", async () => {
  const catalog = await knowledge.loadKnowledgeCatalog();
  const paths = new Set([
    ...catalog.skills.get("analyze-business-meeting").files,
    ...catalog.skills.get("optimize-inventory-cash-flow").files
  ]);
  const privateSourceTerms = [
    "Jacob" + " Flooring",
    "Flooring-" + "Speaker-Map",
    "Flooring-" + "Meeting-Transcript",
    "/" + "Users/",
    "Speaker" + "0",
    "Speaker" + " 0"
  ];
  for (const path of paths) {
    const content = catalog.documents.get(path);
    for (const term of privateSourceTerms) {
      assert.ok(!content.includes(term), `${path} leaked private source marker ${term}`);
    }
  }
});

test("legacy knowledge loading reconstructs all 26 skills in deterministic batches of at most 24", async () => {
  const catalog = await knowledge.loadKnowledgeCatalog();
  const skillIds = [...catalog.skills.keys()].sort();
  const batches = [skillIds.slice(0, 24), skillIds.slice(24)];
  assert.deepEqual(batches.map((batch) => batch.length), [24, 2]);
  const reconstructed = new Map();
  for (const batch of batches) {
    const batchReconstructed = new Map();
    let cursor;
    do {
      const page = await knowledge.loadKnowledgeBundle({
        skill_ids: batch,
        cursor,
        page_size_chars: 30_000
      });
      for (const chunk of page.chunks) {
        const current = batchReconstructed.get(chunk.path) ?? "";
        assert.equal(current.length, chunk.start_character);
        batchReconstructed.set(chunk.path, current + chunk.content);
      }
      cursor = page.next_cursor ?? undefined;
    } while (cursor);
    for (const [path, content] of batchReconstructed) {
      assert.equal(content, catalog.documents.get(path), `legacy batch drifted in ${path}`);
      if (reconstructed.has(path)) assert.equal(reconstructed.get(path), content);
      reconstructed.set(path, content);
    }
  }
  assert.deepEqual(new Set(reconstructed.keys()), new Set(catalog.documents.keys()));
  for (const [path, content] of reconstructed) {
    assert.equal(content, catalog.documents.get(path), `legacy batches drifted in ${path}`);
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

test("Streamable HTTP preserves the three legacy tools and exposes the permanent v0.6 contract", async () => {
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
    [
      "live_consultant_status",
      "load_knowledge_bundle",
      "load_live_consultant_bundle",
      "route_consultation",
      "start_live_consultation"
    ]
  );
  const legacyNames = new Set([
    "route_consultation",
    "load_knowledge_bundle",
    "live_consultant_status"
  ]);
  const actualLegacyContract = list.result.tools.filter((tool) => legacyNames.has(tool.name));
  assert.deepEqual(actualLegacyContract, legacyToolContract);
  assert.deepEqual(list.result.tools, currentToolContract);
  assert.equal(
    contractHash(actualLegacyContract),
    "b735cd0f2fafcf309e7cf88cda2efdabdd7f9e7b5f2f3dc6d7b5a849a177afdb"
  );
  assert.equal(
    contractHash(list.result.tools),
    "555d632d8680565071d606b011068efa57f8d9109f5b2093550f2020d627b8df"
  );
  const schemas = Object.fromEntries(
    actualLegacyContract.map((tool) => [tool.name, tool.inputSchema])
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

  const startCall = await rpc(POST, {
    jsonrpc: "2.0",
    id: 6,
    method: "tools/call",
    params: {
      name: "start_live_consultation",
      arguments: {
        query: "Build a complete acquisition offer for a Toronto HVAC company",
        business_context: "Local service business selling to homeowners",
        client: {
          plugin_version: "0.6.0",
          supported_contract_versions: ["1.0.0"],
          capabilities: ["same-task-hosted-updates"]
        }
      }
    }
  });
  assert.equal(startCall.result.isError, undefined);
  assert.equal(startCall.result.structuredContent.contract_version, "1.0.0");
  assert.equal(startCall.result.structuredContent.compatibility.same_task_compatible, true);
  assert.match(startCall.result.structuredContent.runtime_directives.digest, /^[0-9a-f]{64}$/);

  const liveBundleCall = await rpc(POST, {
    jsonrpc: "2.0",
    id: 7,
    method: "tools/call",
    params: {
      name: "load_live_consultant_bundle",
      arguments: {
        consultation_id: startCall.result.structuredContent.consultation_id,
        page_size_chars: 2_000
      }
    }
  });
  assert.equal(liveBundleCall.result.isError, undefined);
  assert.equal(
    liveBundleCall.result.structuredContent.knowledge_digest,
    startCall.result.structuredContent.knowledge_digest
  );
  assert.ok(liveBundleCall.result.structuredContent.chunks.length > 0);
});

test("v0.6 consultation IDs exclude prompts and reconstruct one pinned knowledge bundle", async () => {
  const privateQuerySentinel = "PRIVATE-QUERY-SENTINEL-7f4c";
  const privateContextSentinel = "PRIVATE-CONTEXT-SENTINEL-93ab";
  const privateClientSentinel = "PRIVATE-CLIENT-SENTINEL-22de";
  const started = await runtime.startLiveConsultation({
    query: `Use Sell Like Crazy for ${privateQuerySentinel}`,
    business_context: privateContextSentinel,
    client: {
      plugin_version: "0.6.0",
      supported_contract_versions: ["1.0.0"],
      extensions: { test: privateClientSentinel }
    }
  });
  const decodedToken = Buffer.from(started.consultation_id, "base64url").toString("utf8");
  assert.doesNotMatch(decodedToken, new RegExp(privateQuerySentinel));
  assert.doesNotMatch(decodedToken, new RegExp(privateContextSentinel));
  assert.doesNotMatch(decodedToken, new RegExp(privateClientSentinel));
  assert.doesNotMatch(decodedToken, /business_context|query|client/);

  const catalog = await knowledge.loadKnowledgeCatalog();
  const selectedSkillIds = started.selected_skills.map((skill) => skill.skill_id).sort();
  const expectedPaths = new Set(
    selectedSkillIds.flatMap((skillId) => catalog.skills.get(skillId).files)
  );
  const reconstructed = new Map();
  let cursor;
  let pages = 0;
  do {
    const page = await runtime.loadLiveConsultantBundle({
      consultation_id: started.consultation_id,
      cursor,
      page_size_chars: 2_000
    });
    pages += 1;
    assert.equal(page.consultation_id, started.consultation_id);
    assert.equal(page.knowledge_digest, started.knowledge_digest);
    assert.equal(page.runtime_directives_version, started.runtime_directives.version);
    for (const chunk of page.chunks) {
      const current = reconstructed.get(chunk.path) ?? "";
      assert.equal(current.length, chunk.start_character);
      reconstructed.set(chunk.path, current + chunk.content);
    }
    cursor = page.next_cursor ?? undefined;
  } while (cursor);

  assert.ok(pages > 1);
  assert.deepEqual(new Set(reconstructed.keys()), expectedPaths);
  for (const [path, content] of reconstructed) {
    assert.equal(content, catalog.documents.get(path), `hosted v0.6 content drifted for ${path}`);
  }
});

test("v0.6 compatibility metadata rejects malformed clients and fails closed for unsupported clients", async () => {
  const { POST } = await import("../app/[transport]/route.js");
  for (const client of [
    { supported_contract_versions: [] },
    { plugin_version: "0.6" }
  ]) {
    const rejected = await rpc(POST, {
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: {
        name: "start_live_consultation",
        arguments: { query: "test compatibility metadata", client }
      }
    });
    assert.equal(rejected.result.isError, true);
    assert.match(rejected.result.content[0].text, /Input validation error/);
  }

  for (const client of [
    { supported_contract_versions: [] },
    { supported_contract_versions: ["9.0.0"] },
    { plugin_version: "not-semver" },
    { plugin_version: "0.5.1", supported_contract_versions: ["1.0.0"] }
  ]) {
    const result = await runtime.startLiveConsultation({
      query: "test compatibility metadata",
      client
    });
    assert.equal(result.compatibility.status, "upgrade_required");
    assert.equal(result.compatibility.same_task_compatible, false);
  }
});

test("v0.6 tokens and cursors fail closed without leaking consultation data", async () => {
  const first = await runtime.startLiveConsultation({ query: "Sell Like Crazy offer" });
  const second = await runtime.startLiveConsultation({ query: "Meta ads audit" });
  const firstPage = await runtime.loadLiveConsultantBundle({
    consultation_id: first.consultation_id,
    page_size_chars: 2_000
  });
  assert.ok(firstPage.next_cursor);

  const replacement = first.consultation_id.endsWith("A") ? "B" : "A";
  const tamperedConsultation = `${first.consultation_id.slice(0, -1)}${replacement}`;
  await assert.rejects(
    runtime.loadLiveConsultantBundle({ consultation_id: tamperedConsultation }),
    /INVALID_CONSULTATION_ID/
  );
  const nullEnvelope = {
    payload: null,
    checksum: testTokenMac("live-consultant-consultation-v1", null)
  };
  await assert.rejects(
    runtime.loadLiveConsultantBundle({
      consultation_id: Buffer.from(canonicalJson(nullEnvelope), "utf8").toString("base64url")
    }),
    /INVALID_CONSULTATION_ID/
  );
  await assert.rejects(
    runtime.loadLiveConsultantBundle({
      consultation_id: second.consultation_id,
      cursor: firstPage.next_cursor,
      page_size_chars: 2_000
    }),
    /CURSOR_CONSULTATION_MISMATCH/
  );

  const envelope = JSON.parse(Buffer.from(first.consultation_id, "base64url").toString("utf8"));
  envelope.payload.skill_ids = ["founder-business-consultant"];
  envelope.checksum = createHash("sha256")
    .update("live-consultant-consultation-v1")
    .update("\0")
    .update(canonicalJson(envelope.payload))
    .digest("hex");
  const publiclyRechecksummed = Buffer.from(canonicalJson(envelope), "utf8").toString("base64url");
  await assert.rejects(
    runtime.loadLiveConsultantBundle({ consultation_id: publiclyRechecksummed }),
    /INVALID_CONSULTATION_ID/
  );

  const signedUnknownEnvelope = JSON.parse(
    Buffer.from(first.consultation_id, "base64url").toString("utf8")
  );
  signedUnknownEnvelope.payload.skill_ids = ["not-a-real-live-consultant-skill"];
  signedUnknownEnvelope.checksum = testTokenMac(
    "live-consultant-consultation-v1",
    signedUnknownEnvelope.payload
  );
  const signedUnknownConsultation = Buffer.from(
    canonicalJson(signedUnknownEnvelope),
    "utf8"
  ).toString("base64url");
  await assert.rejects(
    runtime.loadLiveConsultantBundle({ consultation_id: signedUnknownConsultation }),
    /INVALID_CONSULTATION_ID|unknown skill/
  );

  const cursorEnvelope = JSON.parse(
    Buffer.from(firstPage.next_cursor, "base64url").toString("utf8")
  );
  cursorEnvelope.payload.offset += 4_000;
  cursorEnvelope.checksum = createHash("sha256")
    .update("live-consultant-bundle-cursor-v1")
    .update("\0")
    .update(canonicalJson(cursorEnvelope.payload))
    .digest("hex");
  const publiclyRechecksummedCursor = Buffer.from(
    canonicalJson(cursorEnvelope),
    "utf8"
  ).toString("base64url");
  await assert.rejects(
    runtime.loadLiveConsultantBundle({
      consultation_id: first.consultation_id,
      cursor: publiclyRechecksummedCursor,
      page_size_chars: 2_000
    }),
    /INVALID_CURSOR/
  );

  const realCatalog = await knowledge.loadKnowledgeCatalog();
  const retiredCatalog = { ...realCatalog, digest: "0".repeat(64) };
  knowledge.registerKnowledgeCatalogForTests(retiredCatalog, { current: true });
  const retired = await runtime.startLiveConsultation({ query: "Business audit" });
  knowledge.resetKnowledgeCacheForTests();
  await assert.rejects(
    runtime.loadLiveConsultantBundle({ consultation_id: retired.consultation_id }),
    (error) => {
      assert.match(error.message, /KNOWLEDGE_VERSION_UNAVAILABLE/);
      assert.doesNotMatch(error.message, /Sell Like Crazy|Meta ads|PRIVATE/);
      return true;
    }
  );
  await knowledge.loadKnowledgeCatalog();
});

test("one initialized MCP client receives compatible knowledge and directive updates on later calls", async () => {
  const { POST } = await import("../app/[transport]/route.js");
  const catalogA = await knowledge.loadKnowledgeCatalog();
  let initializeCount = 0;
  let listCount = 0;
  initializeCount += 1;
  await rpc(POST, {
    jsonrpc: "2.0",
    id: 101,
    method: "initialize",
    params: {
      protocolVersion: "2025-03-26",
      capabilities: {},
      clientInfo: { name: "same-task-transition-test", version: "1.0.0" }
    }
  });
  listCount += 1;
  await rpc(POST, { jsonrpc: "2.0", id: 102, method: "tools/list", params: {} });

  const startA = await rpc(POST, {
    jsonrpc: "2.0",
    id: 103,
    method: "tools/call",
    params: {
      name: "start_live_consultation",
      arguments: { query: "Audit a local service business" }
    }
  });
  const valueA = startA.result.structuredContent;

  const updatedPath = catalogA.skills.get("audit-business").files[0];
  const updatedDocuments = new Map(catalogA.documents);
  updatedDocuments.set(
    updatedPath,
    `DEPLOYMENT-B-KNOWLEDGE-SENTINEL\n${updatedDocuments.get(updatedPath)}`
  );
  const catalogB = {
    ...catalogA,
    pluginManifest: { ...catalogA.pluginManifest, version: "0.6.1+test" },
    releaseMarker: {
      ...(catalogA.releaseMarker ?? {}),
      version: "0.6.1",
      source_commit: "b".repeat(40)
    },
    routingFixtures: {
      ...catalogA.routingFixtures,
      fixtures: [
        ...(catalogA.routingFixtures.fixtures ?? []),
        {
          id: "deployment-b-routing-sentinel",
          prompt_summary: "Audit a local service business",
          routing_section: "deployment b routing update",
          required_skills: ["founder-playbook-monetizing-innovation"]
        }
      ]
    },
    documents: updatedDocuments,
    digest: "b".repeat(64)
  };
  knowledge.resetKnowledgeCacheForTests();
  knowledge.registerKnowledgeCatalogForTests(catalogB, { current: true });

  try {
    const startB = await rpc(POST, {
      jsonrpc: "2.0",
      id: 104,
      method: "tools/call",
      params: {
        name: "start_live_consultation",
        arguments: { query: "Audit a local service business" }
      }
    });
    const valueB = startB.result.structuredContent;
    assert.equal(valueB.contract_version, valueA.contract_version);
    assert.equal(valueB.knowledge_digest, catalogB.digest);
    assert.notEqual(valueB.knowledge_digest, valueA.knowledge_digest);
    assert.equal(valueB.public_release_version, "0.6.1");
    assert.ok(!valueA.matched_routing_fixtures.includes("deployment-b-routing-sentinel"));
    assert.ok(valueB.matched_routing_fixtures.includes("deployment-b-routing-sentinel"));
    assert.ok(
      valueB.selected_skills.some(
        (skill) => skill.skill_id === "founder-playbook-monetizing-innovation"
      )
    );
    assert.equal(initializeCount, 1);
    assert.equal(listCount, 1);

    const oldKnowledgeLoad = await rpc(POST, {
      jsonrpc: "2.0",
      id: 105,
      method: "tools/call",
      params: {
        name: "load_live_consultant_bundle",
        arguments: { consultation_id: valueA.consultation_id }
      }
    });
    assert.equal(oldKnowledgeLoad.result.isError, true);
    assert.match(oldKnowledgeLoad.result.content[0].text, /KNOWLEDGE_VERSION_UNAVAILABLE/);

    let updatedCursor;
    let updatedKnowledge = "";
    let callId = 106;
    do {
      const pageCall = await rpc(POST, {
        jsonrpc: "2.0",
        id: callId,
        method: "tools/call",
        params: {
          name: "load_live_consultant_bundle",
          arguments: {
            consultation_id: valueB.consultation_id,
            cursor: updatedCursor,
            page_size_chars: 30_000
          }
        }
      });
      assert.equal(pageCall.result.isError, undefined);
      assert.equal(pageCall.result.structuredContent.knowledge_digest, catalogB.digest);
      updatedKnowledge += pageCall.result.structuredContent.chunks
        .map((chunk) => chunk.content)
        .join("");
      updatedCursor = pageCall.result.structuredContent.next_cursor ?? undefined;
      callId += 1;
    } while (updatedCursor);
    assert.match(updatedKnowledge, /DEPLOYMENT-B-KNOWLEDGE-SENTINEL/);

    runtime.registerRuntimeDirectivesForTests({
      schema_version: 1,
      contract_version: "1.0.0",
      directives_version: "1.0.1",
      minimum_plugin_version: "0.6.0",
      content: "UPDATED-DIRECTIVE-SENTINEL. Load every selected page before synthesizing."
    });
    const startC = await rpc(POST, {
      jsonrpc: "2.0",
      id: callId,
      method: "tools/call",
      params: {
        name: "start_live_consultation",
        arguments: { query: "Audit a local service business" }
      }
    });
    callId += 1;
    const valueC = startC.result.structuredContent;
    assert.equal(valueC.knowledge_digest, valueB.knowledge_digest);
    assert.equal(valueC.runtime_directives.version, "1.0.1");
    assert.match(valueC.runtime_directives.content, /UPDATED-DIRECTIVE-SENTINEL/);
    assert.notEqual(valueC.runtime_directives.digest, valueB.runtime_directives.digest);

    const oldDirectiveLoad = await rpc(POST, {
      jsonrpc: "2.0",
      id: callId,
      method: "tools/call",
      params: {
        name: "load_live_consultant_bundle",
        arguments: { consultation_id: valueB.consultation_id }
      }
    });
    callId += 1;
    assert.equal(oldDirectiveLoad.result.isError, true);
    assert.match(oldDirectiveLoad.result.content[0].text, /KNOWLEDGE_VERSION_UNAVAILABLE/);

    const currentLoad = await rpc(POST, {
      jsonrpc: "2.0",
      id: callId,
      method: "tools/call",
      params: {
        name: "load_live_consultant_bundle",
        arguments: { consultation_id: valueC.consultation_id }
      }
    });
    assert.equal(currentLoad.result.isError, undefined);
    assert.equal(currentLoad.result.structuredContent.runtime_directives_version, "1.0.1");
    assert.equal(initializeCount, 1);
    assert.equal(listCount, 1);
  } finally {
    runtime.resetRuntimeCacheForTests();
    knowledge.resetKnowledgeCacheForTests();
    await knowledge.loadKnowledgeCatalog();
  }
});

test("the v0.6 hosted path can route and fully load every declared skill", async () => {
  const catalog = await knowledge.loadKnowledgeCatalog();
  for (const [skillId, definition] of catalog.skills) {
    const query = definition.triggers?.[0] ?? `${skillId.replaceAll("-", " ")} ${definition.contribution}`;
    const started = await runtime.startLiveConsultation({ query });
    const selectedSkillIds = started.selected_skills.map((skill) => skill.skill_id).sort();
    assert.ok(selectedSkillIds.includes(skillId), `hosted route omitted ${skillId}`);
    const expectedPaths = new Set(
      selectedSkillIds.flatMap((selectedSkillId) => catalog.skills.get(selectedSkillId).files)
    );
    const reconstructed = new Map();
    let cursor;
    do {
      const page = await runtime.loadLiveConsultantBundle({
        consultation_id: started.consultation_id,
        cursor,
        page_size_chars: 30_000
      });
      for (const chunk of page.chunks) {
        const current = reconstructed.get(chunk.path) ?? "";
        assert.equal(current.length, chunk.start_character, `${skillId} has a gap or overlap in ${chunk.path}`);
        reconstructed.set(chunk.path, current + chunk.content);
      }
      cursor = page.next_cursor ?? undefined;
    } while (cursor);
    assert.deepEqual(new Set(reconstructed.keys()), expectedPaths, `${skillId} loaded an incomplete file set`);
    for (const [path, content] of reconstructed) {
      assert.equal(content, catalog.documents.get(path), `${skillId} drifted in ${path}`);
    }
  }
});

test("one v0.6 consultation can pin and fully load the complete 26-skill catalog", async () => {
  const catalog = await knowledge.loadKnowledgeCatalog();
  const query = [...catalog.skills]
    .map(([skillId, definition]) => definition.triggers?.[0] ?? skillId.replaceAll("-", " "))
    .join("; ");
  const started = await runtime.startLiveConsultation({ query });
  const selectedSkillIds = started.selected_skills.map((skill) => skill.skill_id).sort();
  assert.deepEqual(selectedSkillIds, [...catalog.skills.keys()].sort());

  const reconstructed = new Map();
  let cursor;
  do {
    const page = await runtime.loadLiveConsultantBundle({
      consultation_id: started.consultation_id,
      cursor,
      page_size_chars: 30_000
    });
    for (const chunk of page.chunks) {
      const current = reconstructed.get(chunk.path) ?? "";
      assert.equal(current.length, chunk.start_character);
      reconstructed.set(chunk.path, current + chunk.content);
    }
    cursor = page.next_cursor ?? undefined;
  } while (cursor);

  assert.deepEqual(new Set(reconstructed.keys()), new Set(catalog.documents.keys()));
  for (const [path, content] of reconstructed) {
    assert.equal(content, catalog.documents.get(path), `all-skill load drifted in ${path}`);
  }
});

test("missing or short runtime token authentication fails closed and health reports it", async () => {
  runtime.disableRuntimeTokenSecretForTests();
  try {
    await assert.rejects(
      runtime.startLiveConsultation({ query: "Business audit" }),
      /RUNTIME_NOT_READY/
    );
    assert.throws(
      () => runtime.registerRuntimeTokenSecretForTests("too-short"),
      /at least 32 bytes/
    );
    const health = await import("../app/healthz/route.js");
    const unavailable = await health.GET();
    assert.equal(unavailable.status, 503);
    assert.deepEqual(await unavailable.json(), {
      ok: false,
      error: "Live Consultant runtime is unavailable"
    });
  } finally {
    runtime.registerRuntimeTokenSecretForTests(TEST_RUNTIME_SECRET);
  }
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
