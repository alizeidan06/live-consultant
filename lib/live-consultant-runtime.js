import { createHash, createHmac, randomUUID, timingSafeEqual } from "node:crypto";
import { readFile } from "node:fs/promises";

import {
  createKnowledgeBundlePage,
  loadKnowledgeCatalog,
  loadKnowledgeCatalogByDigest,
  routeConsultationWithCatalog
} from "./live-consultant-knowledge.js";

const CONTRACT_VERSION = "1.0.0";
const TOKEN_VERSION = 1;
const MAX_OPAQUE_TOKEN_LENGTH = 8_192;
const DIRECTIVES_URL = new URL("../runtime/runtime-directives.json", import.meta.url);
const SEMVER_PATTERN = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
const DIGEST_PATTERN = /^[0-9a-f]{64}$/;

let directivesPromise;
let tokenSecretOverride;

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

function exactKeys(value, keys) {
  return (
    Boolean(value) &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    JSON.stringify(Object.keys(value).sort()) === JSON.stringify([...keys].sort())
  );
}

export function computeRuntimeDirectivesDigest(value) {
  return createHash("sha256")
    .update("live-consultant-runtime-directives-v1\0")
    .update(canonicalJson(value))
    .digest("hex");
}

async function readRuntimeDirectives() {
  const value = JSON.parse(await readFile(DIRECTIVES_URL, "utf8"));
  if (
    !value ||
    !exactKeys(value, [
      "schema_version",
      "contract_version",
      "directives_version",
      "minimum_plugin_version",
      "content"
    ]) ||
    value.schema_version !== 1 ||
    value.contract_version !== CONTRACT_VERSION ||
    !SEMVER_PATTERN.test(value.directives_version) ||
    !SEMVER_PATTERN.test(value.minimum_plugin_version) ||
    typeof value.content !== "string" ||
    !value.content.trim()
  ) {
    throw new Error("RUNTIME_NOT_READY: hosted directives are invalid");
  }
  return {
    ...value,
    content: value.content.trim(),
    digest: computeRuntimeDirectivesDigest(value)
  };
}

export function resetRuntimeCacheForTests() {
  directivesPromise = undefined;
}

export function registerRuntimeDirectivesForTests(value) {
  if (
    !value ||
    value.schema_version !== 1 ||
    value.contract_version !== CONTRACT_VERSION ||
    !SEMVER_PATTERN.test(value.directives_version) ||
    !SEMVER_PATTERN.test(value.minimum_plugin_version) ||
    typeof value.content !== "string" ||
    !value.content.trim()
  ) {
    throw new Error("test directives are invalid");
  }
  directivesPromise = Promise.resolve({
    ...value,
    content: value.content.trim(),
    digest: computeRuntimeDirectivesDigest(value)
  });
}

export function registerRuntimeTokenSecretForTests(value) {
  if (typeof value !== "string" || Buffer.byteLength(value, "utf8") < 32) {
    throw new Error("test runtime token secret must contain at least 32 bytes");
  }
  tokenSecretOverride = value;
}

export function disableRuntimeTokenSecretForTests() {
  tokenSecretOverride = null;
}

function runtimeTokenSecret() {
  const value = tokenSecretOverride !== undefined
    ? tokenSecretOverride
    : process.env.LIVE_CONSULTANT_TOKEN_SECRET;
  if (typeof value !== "string" || Buffer.byteLength(value, "utf8") < 32) {
    throw new Error("RUNTIME_NOT_READY: hosted token authentication is not configured");
  }
  return value;
}

export function loadRuntimeDirectives() {
  directivesPromise ??= readRuntimeDirectives();
  return directivesPromise;
}

export async function assertLiveConsultantRuntimeReady() {
  runtimeTokenSecret();
  await loadRuntimeDirectives();
}

function integrityDigest(domain, payload) {
  return createHmac("sha256", runtimeTokenSecret())
    .update(domain)
    .update("\0")
    .update(canonicalJson(payload))
    .digest("hex");
}

function equalDigest(left, right) {
  if (
    typeof left !== "string" ||
    typeof right !== "string" ||
    left.length !== right.length
  ) {
    return false;
  }
  return timingSafeEqual(Buffer.from(left, "utf8"), Buffer.from(right, "utf8"));
}

function encodeOpaque(domain, payload) {
  const envelope = {
    payload,
    checksum: integrityDigest(domain, payload)
  };
  return Buffer.from(canonicalJson(envelope), "utf8").toString("base64url");
}

function decodeOpaque(token, domain, errorCode) {
  try {
    if (typeof token !== "string" || !token || token.length > MAX_OPAQUE_TOKEN_LENGTH) {
      throw new Error();
    }
    const decoded = Buffer.from(token, "base64url").toString("utf8");
    if (Buffer.from(decoded, "utf8").toString("base64url") !== token) {
      throw new Error();
    }
    const envelope = JSON.parse(decoded);
    if (
      !envelope ||
      !exactKeys(envelope, ["payload", "checksum"]) ||
      !envelope.payload ||
      typeof envelope.payload !== "object" ||
      Array.isArray(envelope.payload) ||
      !equalDigest(envelope.checksum, integrityDigest(domain, envelope.payload))
    ) {
      throw new Error();
    }
    return envelope.payload;
  } catch (error) {
    if ((error?.message ?? "").startsWith("RUNTIME_NOT_READY:")) throw error;
    throw new Error(`${errorCode}: opaque runtime token is invalid`);
  }
}

function validSkillIds(value) {
  return (
    Array.isArray(value) &&
    value.length >= 1 &&
    value.length <= 24 &&
    new Set(value).size === value.length &&
    value.every((item) => typeof item === "string" && item.length >= 1 && item.length <= 200)
  );
}

function encodeConsultationId({ catalog, directives, selectedSkillIds }) {
  return encodeOpaque("live-consultant-consultation-v1", {
    v: TOKEN_VERSION,
    contract_version: CONTRACT_VERSION,
    knowledge_digest: catalog.digest,
    directives_version: directives.directives_version,
    directives_digest: directives.digest,
    skill_ids: [...selectedSkillIds].sort(),
    nonce: randomUUID()
  });
}

function decodeConsultationId(consultationId) {
  const payload = decodeOpaque(
    consultationId,
    "live-consultant-consultation-v1",
    "INVALID_CONSULTATION_ID"
  );
  if (
    !exactKeys(payload, [
      "v",
      "contract_version",
      "knowledge_digest",
      "directives_version",
      "directives_digest",
      "skill_ids",
      "nonce"
    ]) ||
    payload.v !== TOKEN_VERSION ||
    payload.contract_version !== CONTRACT_VERSION ||
    !DIGEST_PATTERN.test(payload.knowledge_digest) ||
    !SEMVER_PATTERN.test(payload.directives_version) ||
    !DIGEST_PATTERN.test(payload.directives_digest) ||
    !validSkillIds(payload.skill_ids) ||
    typeof payload.nonce !== "string" ||
    !/^[0-9a-f-]{36}$/.test(payload.nonce)
  ) {
    throw new Error("INVALID_CONSULTATION_ID: opaque runtime token is invalid");
  }
  return payload;
}

function consultationFingerprint(consultationId) {
  return createHash("sha256")
    .update("live-consultant-consultation-fingerprint-v1\0")
    .update(consultationId)
    .digest("hex");
}

function encodeBundleCursor(consultationId, offset) {
  return encodeOpaque("live-consultant-bundle-cursor-v1", {
    v: TOKEN_VERSION,
    consultation_fingerprint: consultationFingerprint(consultationId),
    offset
  });
}

function decodeBundleCursor(cursor, consultationId) {
  const payload = decodeOpaque(cursor, "live-consultant-bundle-cursor-v1", "INVALID_CURSOR");
  if (
    !exactKeys(payload, ["v", "consultation_fingerprint", "offset"]) ||
    payload.v !== TOKEN_VERSION ||
    !DIGEST_PATTERN.test(payload.consultation_fingerprint) ||
    !Number.isInteger(payload.offset) ||
    payload.offset < 0
  ) {
    throw new Error("INVALID_CURSOR: opaque runtime token is invalid");
  }
  if (payload.consultation_fingerprint !== consultationFingerprint(consultationId)) {
    throw new Error("CURSOR_CONSULTATION_MISMATCH: cursor belongs to another consultation");
  }
  return payload.offset;
}

function parseSemver(value) {
  const match = typeof value === "string" ? SEMVER_PATTERN.exec(value.split("+", 1)[0]) : null;
  return match ? match.slice(1).map(Number) : null;
}

function isOlderVersion(candidate, minimum) {
  const left = parseSemver(candidate);
  const right = parseSemver(minimum);
  if (!left || !right) return false;
  for (let index = 0; index < 3; index += 1) {
    if (left[index] !== right[index]) return left[index] < right[index];
  }
  return false;
}

function compatibilityFor(client, directives) {
  const supported = client?.supported_contract_versions;
  if (
    supported !== undefined &&
    (!Array.isArray(supported) ||
      supported.length === 0 ||
      supported.some((value) => !SEMVER_PATTERN.test(value)) ||
      !supported.includes(CONTRACT_VERSION))
  ) {
    return {
      status: "upgrade_required",
      minimum_plugin_version: directives.minimum_plugin_version,
      same_task_compatible: false,
      message: "This client did not declare support for the hosted contract. Upgrade Live Consultant and open a new Codex task."
    };
  }
  if (
    client?.plugin_version !== undefined &&
    (!parseSemver(client.plugin_version) ||
      isOlderVersion(client.plugin_version, directives.minimum_plugin_version))
  ) {
    return {
      status: "upgrade_required",
      minimum_plugin_version: directives.minimum_plugin_version,
      same_task_compatible: false,
      message: "Upgrade Live Consultant and open one new Codex task to activate the permanent hosted contract."
    };
  }
  return {
    status: "compatible",
    minimum_plugin_version: directives.minimum_plugin_version,
    same_task_compatible: true,
    message: "Compatible hosted updates are available in this same task on its next Live Consultant call."
  };
}

export async function startLiveConsultation({ query, business_context = "", client }) {
  const [catalog, directives] = await Promise.all([
    loadKnowledgeCatalog(),
    loadRuntimeDirectives()
  ]);
  const route = routeConsultationWithCatalog(catalog, { query, business_context });
  const selectedSkillIds = route.selected_skills.map((skill) => skill.skill_id);
  const consultationId = encodeConsultationId({ catalog, directives, selectedSkillIds });
  const marker = catalog.releaseMarker ?? {};

  return {
    contract_version: CONTRACT_VERSION,
    consultation_id: consultationId,
    knowledge_digest: catalog.digest,
    plugin_version: catalog.pluginManifest.version,
    public_release_version: marker.version ?? null,
    runtime_directives: {
      version: directives.directives_version,
      digest: directives.digest,
      content: directives.content
    },
    selected_skills: route.selected_skills,
    matched_routing_fixtures: route.matched_routing_fixtures,
    niche_decision_fields: route.niche_decision_fields,
    compatibility: compatibilityFor(client, directives),
    next_step: "Call load_live_consultant_bundle with this consultation_id and continue until next_cursor is null before synthesizing advice.",
    extensions: {}
  };
}

export async function loadLiveConsultantBundle({
  consultation_id,
  cursor,
  page_size_chars = 12_000
}) {
  const claims = decodeConsultationId(consultation_id);
  const directives = await loadRuntimeDirectives();
  if (
    claims.directives_version !== directives.directives_version ||
    claims.directives_digest !== directives.digest
  ) {
    throw new Error("KNOWLEDGE_VERSION_UNAVAILABLE: start a new consultation in this same task and reload from page one");
  }
  const catalog = await loadKnowledgeCatalogByDigest(claims.knowledge_digest);
  if (!catalog) {
    throw new Error("KNOWLEDGE_VERSION_UNAVAILABLE: start a new consultation in this same task and reload from page one");
  }
  const offset = cursor === undefined ? 0 : decodeBundleCursor(cursor, consultation_id);
  let page;
  try {
    page = createKnowledgeBundlePage(catalog, {
      skill_ids: claims.skill_ids,
      offset,
      page_size_chars
    });
  } catch (error) {
    if (/offset/.test(error?.message ?? "")) {
      throw new Error("INVALID_CURSOR: cursor offset is outside the consultation bundle");
    }
    throw error;
  }
  const nextCursor = page.page_end_character < page.total_characters
    ? encodeBundleCursor(consultation_id, page.page_end_character)
    : null;

  return {
    contract_version: CONTRACT_VERSION,
    consultation_id,
    runtime_directives_version: directives.directives_version,
    runtime_directives_digest: directives.digest,
    schema_version: page.schema_version,
    knowledge_digest: page.knowledge_digest,
    selected_skill_ids: page.selected_skill_ids,
    files_total: page.files_total,
    total_characters: page.total_characters,
    page_start_character: page.page_start_character,
    page_end_character: page.page_end_character,
    chunks: page.chunks,
    next_cursor: nextCursor,
    complete: nextCursor === null,
    instruction: nextCursor
      ? "Call load_live_consultant_bundle again with the same consultation_id and next_cursor."
      : "The complete pinned knowledge bundle is loaded. Apply the returned runtime directives and synthesize the consultation.",
    extensions: {}
  };
}
