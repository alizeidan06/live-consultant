import { createHash } from "node:crypto";
import { lstat, readFile, readdir, realpath } from "node:fs/promises";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const MODULE_DIRECTORY = dirname(fileURLToPath(import.meta.url));
const MANIFEST_PATH = "assets/skill-knowledge-manifest.json";
const ROUTING_FIXTURES_PATH = "assets/skill-routing-fixtures.json";
const PLUGIN_MANIFEST_PATH = ".codex-plugin/plugin.json";
const DEFAULT_PAGE_SIZE = 12_000;
const MIN_PAGE_SIZE = 2_000;
const MAX_PAGE_SIZE = 30_000;
const MAX_QUERY_LENGTH = 12_000;
const MAX_BUSINESS_CONTEXT_LENGTH = 4_000;
const LEGACY_SKILL_BATCH_SIZE = 24;
const RUNTIME_SCHEMA_VERSION = "1.0.0";

const STOP_WORDS = new Set([
  "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
  "i", "in", "into", "is", "it", "my", "of", "on", "or", "our", "the",
  "then", "this", "to", "we", "what", "with", "you", "your"
]);

const NICHE_FIELDS = [
  "decision_requested",
  "vertical_and_category",
  "exact_buyer",
  "user_payer_decision_maker",
  "trigger_job_pain_or_progress",
  "offer_price_and_delivery",
  "business_model_and_sales_motion",
  "geography_language_and_currency",
  "acquisition_or_sales_channel",
  "stage_capacity_and_evidence",
  "alternatives_and_workaround",
  "current_phase"
];

let catalogPromise;
const catalogRegistry = new Map();

function inside(root, target) {
  const path = relative(root, target);
  return path === "" || (!path.startsWith(`..${sep}`) && path !== ".." && !isAbsolute(path));
}

async function findPluginRoot() {
  const candidates = [
    resolve(MODULE_DIRECTORY, "../plugins/live-consultant"),
    resolve(MODULE_DIRECTORY, "../../../plugins/live-consultant")
  ];

  for (const candidate of candidates) {
    try {
      const root = await realpath(candidate);
      const manifest = resolve(root, MANIFEST_PATH);
      const stat = await lstat(manifest);
      if (stat.isFile() && !stat.isSymbolicLink()) {
        return root;
      }
    } catch {
      // Try the next deterministic location.
    }
  }
  throw new Error("Live Consultant public knowledge package is unavailable");
}

async function safeTarget(root, relativePath, expectedType = "file") {
  if (typeof relativePath !== "string" || !relativePath || isAbsolute(relativePath)) {
    throw new Error("Knowledge manifest contains an invalid relative path");
  }
  const target = resolve(root, relativePath);
  if (!inside(root, target)) {
    throw new Error("Knowledge path escapes the public plugin root");
  }
  const stat = await lstat(target);
  if (stat.isSymbolicLink()) {
    throw new Error("Symbolic links are not allowed in the public knowledge package");
  }
  const resolvedTarget = await realpath(target);
  if (!inside(root, resolvedTarget)) {
    throw new Error("Knowledge path resolves outside the public plugin root");
  }
  if (expectedType === "file" && !stat.isFile()) {
    throw new Error("Knowledge manifest path is not a file");
  }
  if (expectedType === "directory" && !stat.isDirectory()) {
    throw new Error("Knowledge manifest path is not a directory");
  }
  return target;
}

async function markdownFiles(root, relativeDirectory) {
  const directory = await safeTarget(root, relativeDirectory, "directory");
  const files = [];

  async function walk(current) {
    const entries = await readdir(current, { withFileTypes: true });
    entries.sort((left, right) => left.name.localeCompare(right.name));
    for (const entry of entries) {
      const target = resolve(current, entry.name);
      const stat = await lstat(target);
      if (stat.isSymbolicLink()) {
        throw new Error("Symbolic links are not allowed in the public knowledge package");
      }
      if (stat.isDirectory()) {
        await walk(target);
      } else if (stat.isFile() && entry.name.endsWith(".md")) {
        const path = relative(root, target).split(sep).join("/");
        await safeTarget(root, path, "file");
        files.push(path);
      }
    }
  }

  await walk(directory);
  return files;
}

async function readJson(root, relativePath) {
  const path = await safeTarget(root, relativePath, "file");
  return JSON.parse(await readFile(path, "utf8"));
}

async function readOptionalReleaseMarker(root) {
  const target = resolve(root, "../../.live-consultant-public-export.json");
  try {
    const stat = await lstat(target);
    if (!stat.isFile() || stat.isSymbolicLink()) {
      throw new Error("Public release marker is not a regular file");
    }
    return JSON.parse(await readFile(target, "utf8"));
  } catch (error) {
    if (error?.code === "ENOENT") return null;
    throw error;
  }
}

function canonicalJson(value) {
  if (Array.isArray(value)) {
    return `[${value.map((item) => canonicalJson(item)).join(",")}]`;
  }
  if (value && typeof value === "object") {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

export function computeKnowledgeIdentityDigest({
  manifest,
  routingFixtures,
  pluginManifest,
  releaseMarker,
  documents,
  runtimeSchemaVersion = RUNTIME_SCHEMA_VERSION
}) {
  const digest = createHash("sha256");
  digest.update("live-consultant-control-plane\0");
  digest.update(canonicalJson({
    runtime_schema_version: runtimeSchemaVersion,
    plugin_manifest: pluginManifest,
    release_marker: releaseMarker,
    skill_knowledge_manifest: manifest,
    skill_routing_fixtures: routingFixtures
  }));
  digest.update("\0live-consultant-documents\0");
  for (const path of [...documents.keys()].sort()) {
    digest.update(path);
    digest.update("\0");
    digest.update(documents.get(path));
    digest.update("\0");
  }
  return digest.digest("hex");
}

function validateManifest(manifest) {
  if (
    !manifest ||
    manifest.schema_version !== 1 ||
    manifest.bundle_semantics !== "complete_recursive_markdown_plus_declared_files" ||
    !manifest.skills ||
    typeof manifest.skills !== "object"
  ) {
    throw new Error("Unsupported Live Consultant knowledge manifest");
  }
}

async function buildCatalog() {
  const root = await findPluginRoot();
  const manifest = await readJson(root, MANIFEST_PATH);
  const routingFixtures = await readJson(root, ROUTING_FIXTURES_PATH);
  const pluginManifest = await readJson(root, PLUGIN_MANIFEST_PATH);
  const releaseMarker = await readOptionalReleaseMarker(root);
  validateManifest(manifest);

  const skills = new Map();
  const documents = new Map();
  for (const [skillId, definition] of Object.entries(manifest.skills)) {
    const files = new Set();
    for (const bundleRoot of definition.bundle_roots ?? []) {
      for (const path of await markdownFiles(root, bundleRoot)) {
        files.add(path);
      }
    }
    for (const bundleFile of definition.bundle_files ?? []) {
      await safeTarget(root, bundleFile, "file");
      files.add(bundleFile);
    }
    if (files.size === 0) {
      throw new Error(`Knowledge bundle is empty: ${skillId}`);
    }
    const orderedFiles = [...files].sort();
    for (const path of orderedFiles) {
      if (!documents.has(path)) {
        const target = await safeTarget(root, path, "file");
        documents.set(path, await readFile(target, "utf8"));
      }
    }
    skills.set(skillId, { ...definition, files: orderedFiles });
  }

  const digest = computeKnowledgeIdentityDigest({
    manifest,
    routingFixtures,
    pluginManifest,
    releaseMarker,
    documents
  });

  return {
    root,
    manifest,
    routingFixtures,
    pluginManifest,
    releaseMarker,
    skills,
    documents,
    digest
  };
}

export function resetKnowledgeCacheForTests() {
  catalogPromise = undefined;
  catalogRegistry.clear();
}

export function loadKnowledgeCatalog() {
  catalogPromise ??= buildCatalog().then((catalog) => {
    catalogRegistry.set(catalog.digest, catalog);
    return catalog;
  });
  return catalogPromise;
}

export async function loadKnowledgeCatalogByDigest(digest) {
  if (typeof digest !== "string" || !/^[0-9a-f]{64}$/.test(digest)) {
    return null;
  }
  const current = await loadKnowledgeCatalog();
  return catalogRegistry.get(digest) ?? (current.digest === digest ? current : null);
}

export function registerKnowledgeCatalogForTests(catalog, { current = false } = {}) {
  if (!catalog || typeof catalog.digest !== "string") {
    throw new Error("test catalog must have a digest");
  }
  catalogRegistry.set(catalog.digest, catalog);
  if (current) catalogPromise = Promise.resolve(catalog);
}

function normalized(value) {
  return value
    .toLocaleLowerCase("en")
    .normalize("NFKD")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function tokens(value) {
  return new Set(
    normalized(value)
      .split(/\s+/)
      .filter((token) => token.length > 1 && !STOP_WORDS.has(token))
  );
}

function overlapScore(queryTokens, phrase) {
  const phraseTokens = tokens(phrase);
  if (!phraseTokens.size) return 0;
  let overlap = 0;
  for (const token of phraseTokens) {
    if (queryTokens.has(token)) overlap += 1;
  }
  return overlap / phraseTokens.size;
}

function phraseScore(searchText, queryTokens, phrase) {
  const candidate = normalized(phrase);
  if (!candidate) return 0;
  if (searchText.includes(candidate)) return 12 + tokens(candidate).size;
  return overlapScore(queryTokens, candidate) * 6;
}

function declaredPhraseMatches(searchText, phrase) {
  const candidate = normalized(phrase);
  return candidate.length > 0 && ` ${searchText} `.includes(` ${candidate} `);
}

function boundedText(value, maximum, label) {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${label} must be a non-empty string`);
  }
  if (value.length > maximum) {
    throw new Error(`${label} is too long`);
  }
  return value.trim();
}

export function routeConsultationWithCatalog(catalog, { query, business_context = "" }) {
  const cleanQuery = boundedText(query, MAX_QUERY_LENGTH, "query");
  if (
    typeof business_context !== "string" ||
    business_context.length > MAX_BUSINESS_CONTEXT_LENGTH
  ) {
    throw new Error("business_context is too long");
  }
  const searchText = normalized(`${cleanQuery} ${business_context}`);
  const queryTokens = tokens(searchText);
  const scores = new Map();
  const reasons = new Map();

  for (const [skillId, definition] of catalog.skills) {
    const phrases = [skillId.replaceAll("-", " "), definition.contribution, ...(definition.triggers ?? [])];
    const score = Math.max(...phrases.map((phrase) => phraseScore(searchText, queryTokens, phrase)));
    const routingAnchors = definition.routing_anchors ?? [];
    const routingExclusions = definition.routing_exclusions ?? [];
    if (!Array.isArray(routingAnchors) || !Array.isArray(routingExclusions)) {
      throw new Error(`Routing anchors and exclusions must be lists: ${skillId}`);
    }
    const anchorMatched = routingAnchors.length === 0
      || routingAnchors.some((phrase) => declaredPhraseMatches(searchText, phrase));
    const excluded = routingExclusions.some((phrase) =>
      declaredPhraseMatches(searchText, phrase)
    );
    if (score >= 3 && anchorMatched && !excluded) {
      scores.set(skillId, score);
      reasons.set(skillId, "The request matches this skill's declared contribution or triggers.");
    }
  }

  const matchedFixtures = [];
  for (const fixture of catalog.routingFixtures.fixtures ?? []) {
    const summaryOverlap = overlapScore(queryTokens, fixture.prompt_summary ?? "");
    const sectionOverlap = overlapScore(queryTokens, fixture.routing_section ?? "");
    if (summaryOverlap >= 0.45 || sectionOverlap >= 0.75) {
      matchedFixtures.push(fixture.id);
      for (const skillId of fixture.required_skills ?? []) {
        if (!catalog.skills.has(skillId)) {
          throw new Error("Routing fixture references a missing skill");
        }
        scores.set(skillId, Math.max(scores.get(skillId) ?? 0, 20 + summaryOverlap));
        reasons.set(skillId, `Required by the matched ${fixture.id} complete-stack route.`);
      }
    }
  }

  if (catalog.skills.has("founder-business-consultant")) {
    scores.set("founder-business-consultant", Math.max(scores.get("founder-business-consultant") ?? 0, 2));
    reasons.set("founder-business-consultant", "Orchestrates the complete niche-specific skill stack.");
  }

  const companionQueue = [...scores.keys()];
  const expanded = new Set(companionQueue);
  for (let index = 0; index < companionQueue.length; index += 1) {
    const primarySkillId = companionQueue[index];
    const definition = catalog.skills.get(primarySkillId);
    const requiredCompanions = definition?.required_companions ?? [];
    if (!Array.isArray(requiredCompanions)) {
      throw new Error(`Required companions must be a list: ${primarySkillId}`);
    }
    for (const companionSkillId of requiredCompanions) {
      if (typeof companionSkillId !== "string" || !catalog.skills.has(companionSkillId)) {
        throw new Error(`Required companion is missing: ${primarySkillId}`);
      }
      scores.set(companionSkillId, Math.max(scores.get(companionSkillId) ?? 0, 18));
      reasons.set(
        companionSkillId,
        `Required by ${primarySkillId} to complete the requested outcome.`
      );
      if (!expanded.has(companionSkillId)) {
        expanded.add(companionSkillId);
        companionQueue.push(companionSkillId);
      }
    }
  }

  const selectedSkills = [...scores]
    .sort(([leftId, leftScore], [rightId, rightScore]) => rightScore - leftScore || leftId.localeCompare(rightId))
    .map(([skillId, score]) => {
      const definition = catalog.skills.get(skillId);
      return {
        skill_id: skillId,
        contribution: definition.contribution,
        reason: reasons.get(skillId),
        bundle_files: definition.files.length,
        score: Number(score.toFixed(3))
      };
    });

  return {
    schema_version: "1.0.0",
    requested_outcome: cleanQuery,
    selected_skills: selectedSkills,
    matched_routing_fixtures: matchedFixtures,
    niche_decision_fields: NICHE_FIELDS,
    next_step: selectedSkills.length > LEGACY_SKILL_BATCH_SIZE
      ? `Call load_knowledge_bundle in deterministic batches of at most ${LEGACY_SKILL_BATCH_SIZE} selected skill IDs, follow each batch until next_cursor is null, deduplicate shared paths, and load every batch before synthesizing advice.`
      : "Call load_knowledge_bundle for every selected skill and continue until next_cursor is null before synthesizing advice."
  };
}

export async function routeConsultation(input) {
  return routeConsultationWithCatalog(await loadKnowledgeCatalog(), input);
}

function normalizeSkillIds(skillIds, catalog) {
  if (!Array.isArray(skillIds) || skillIds.length === 0 || skillIds.length > catalog.skills.size) {
    throw new Error("skill_ids must contain between one and all available skills");
  }
  const normalizedIds = [...new Set(skillIds)];
  if (normalizedIds.length !== skillIds.length) {
    throw new Error("skill_ids must not contain duplicates");
  }
  for (const skillId of normalizedIds) {
    if (typeof skillId !== "string" || !catalog.skills.has(skillId)) {
      throw new Error("skill_ids contains an unknown skill");
    }
  }
  return normalizedIds.sort();
}

function encodeCursor(payload) {
  const checksum = createHash("sha256")
    .update(payload.digest)
    .update("\0")
    .update(JSON.stringify(payload.skill_ids))
    .update("\0")
    .update(String(payload.offset))
    .digest("hex");
  return Buffer.from(JSON.stringify({ ...payload, checksum }), "utf8").toString("base64url");
}

function decodeCursor(cursor) {
  try {
    const payload = JSON.parse(Buffer.from(cursor, "base64url").toString("utf8"));
    if (
      !payload ||
      typeof payload.digest !== "string" ||
      !Array.isArray(payload.skill_ids) ||
      !Number.isInteger(payload.offset) ||
      typeof payload.checksum !== "string"
    ) {
      throw new Error();
    }
    const expectedChecksum = createHash("sha256")
      .update(payload.digest)
      .update("\0")
      .update(JSON.stringify(payload.skill_ids))
      .update("\0")
      .update(String(payload.offset))
      .digest("hex");
    if (payload.checksum !== expectedChecksum) throw new Error();
    return payload;
  } catch {
    throw new Error("cursor is invalid");
  }
}

function selectedDocuments(skillIds, catalog) {
  const associations = new Map();
  for (const skillId of skillIds) {
    for (const path of catalog.skills.get(skillId).files) {
      const values = associations.get(path) ?? [];
      values.push(skillId);
      associations.set(path, values);
    }
  }
  return [...associations]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([path, skills]) => ({ path, skill_ids: skills.sort(), content: catalog.documents.get(path) }));
}

export function loadKnowledgeBundleFromCatalog(
  catalog,
  { skill_ids, cursor, page_size_chars = DEFAULT_PAGE_SIZE }
) {
  const selectedSkillIds = normalizeSkillIds(skill_ids, catalog);
  if (!Number.isInteger(page_size_chars) || page_size_chars < MIN_PAGE_SIZE || page_size_chars > MAX_PAGE_SIZE) {
    throw new Error(`page_size_chars must be an integer from ${MIN_PAGE_SIZE} to ${MAX_PAGE_SIZE}`);
  }

  let offset = 0;
  if (cursor !== undefined) {
    if (typeof cursor !== "string" || !cursor) throw new Error("cursor is invalid");
    const parsed = decodeCursor(cursor);
    if (
      parsed.digest !== catalog.digest ||
      JSON.stringify(parsed.skill_ids) !== JSON.stringify(selectedSkillIds) ||
      parsed.offset < 0
    ) {
      throw new Error("cursor does not match this knowledge version and skill selection");
    }
    offset = parsed.offset;
  }

  const page = createKnowledgeBundlePage(catalog, {
    skill_ids: selectedSkillIds,
    offset,
    page_size_chars
  });

  const nextCursor = page.page_end_character < page.total_characters
    ? encodeCursor({
        digest: catalog.digest,
        skill_ids: selectedSkillIds,
        offset: page.page_end_character
      })
    : null;

  return {
    ...page,
    next_cursor: nextCursor,
    complete: nextCursor === null,
    instruction: nextCursor ? "Call load_knowledge_bundle again with the same skill_ids and next_cursor." : "The complete selected knowledge bundle has been loaded."
  };
}

export function createKnowledgeBundlePage(
  catalog,
  { skill_ids, offset = 0, page_size_chars = DEFAULT_PAGE_SIZE }
) {
  const selectedSkillIds = normalizeSkillIds(skill_ids, catalog);
  if (!Number.isInteger(page_size_chars) || page_size_chars < MIN_PAGE_SIZE || page_size_chars > MAX_PAGE_SIZE) {
    throw new Error(`page_size_chars must be an integer from ${MIN_PAGE_SIZE} to ${MAX_PAGE_SIZE}`);
  }
  if (!Number.isInteger(offset) || offset < 0) {
    throw new Error("cursor offset is outside the bundle");
  }

  const documents = selectedDocuments(selectedSkillIds, catalog);
  const totalCharacters = documents.reduce((total, document) => total + document.content.length, 0);
  if (offset > totalCharacters) throw new Error("cursor offset is outside the bundle");
  const end = Math.min(offset + page_size_chars, totalCharacters);
  const chunks = [];
  let documentStart = 0;
  for (const document of documents) {
    const documentEnd = documentStart + document.content.length;
    const chunkStart = Math.max(offset, documentStart);
    const chunkEnd = Math.min(end, documentEnd);
    if (chunkStart < chunkEnd) {
      chunks.push({
        path: document.path,
        skill_ids: document.skill_ids,
        start_character: chunkStart - documentStart,
        end_character: chunkEnd - documentStart,
        content: document.content.slice(chunkStart - documentStart, chunkEnd - documentStart)
      });
    }
    documentStart = documentEnd;
    if (documentStart >= end) break;
  }

  return {
    schema_version: "1.0.0",
    knowledge_digest: catalog.digest,
    selected_skill_ids: selectedSkillIds,
    files_total: documents.length,
    total_characters: totalCharacters,
    page_start_character: offset,
    page_end_character: end,
    chunks
  };
}

export async function loadKnowledgeBundle(input) {
  return loadKnowledgeBundleFromCatalog(await loadKnowledgeCatalog(), input);
}

export async function liveConsultantStatus() {
  const catalog = await loadKnowledgeCatalog();
  const marker = catalog.releaseMarker ?? {};
  return {
    service: "live-consultant",
    runtime_schema_version: RUNTIME_SCHEMA_VERSION,
    plugin_version: catalog.pluginManifest.version,
    public_release_version: marker.version ?? null,
    source_commit: marker.source_commit ?? null,
    knowledge_digest: catalog.digest,
    skills: catalog.skills.size,
    knowledge_files: catalog.documents.size,
    persistence: "none",
    external_fetching: false,
    prompt_logging: false,
    update_model: "The stable hosted endpoint serves the knowledge bundled with the current production deployment."
  };
}
