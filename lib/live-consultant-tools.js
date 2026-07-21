import { z } from "zod";

import {
  liveConsultantStatus,
  loadKnowledgeBundle,
  routeConsultation
} from "./live-consultant-knowledge.js";
import {
  loadLiveConsultantBundle,
  startLiveConsultation
} from "./live-consultant-runtime.js";

const READ_ONLY_ANNOTATIONS = {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false
};

const ROUTE_OUTPUT_SCHEMA = {
  schema_version: z.string(),
  requested_outcome: z.string(),
  selected_skills: z.array(z.object({
    skill_id: z.string(),
    contribution: z.string(),
    reason: z.string(),
    bundle_files: z.number().int().nonnegative(),
    score: z.number()
  })),
  matched_routing_fixtures: z.array(z.string()),
  niche_decision_fields: z.array(z.string()),
  next_step: z.string()
};

const BUNDLE_OUTPUT_SCHEMA = {
  schema_version: z.string(),
  knowledge_digest: z.string().regex(/^[0-9a-f]{64}$/),
  selected_skill_ids: z.array(z.string()),
  files_total: z.number().int().nonnegative(),
  total_characters: z.number().int().nonnegative(),
  page_start_character: z.number().int().nonnegative(),
  page_end_character: z.number().int().nonnegative(),
  chunks: z.array(z.object({
    path: z.string(),
    skill_ids: z.array(z.string()),
    start_character: z.number().int().nonnegative(),
    end_character: z.number().int().nonnegative(),
    content: z.string()
  })),
  next_cursor: z.string().nullable(),
  complete: z.boolean(),
  instruction: z.string()
};

const STATUS_OUTPUT_SCHEMA = {
  service: z.literal("live-consultant"),
  runtime_schema_version: z.string(),
  plugin_version: z.string(),
  public_release_version: z.string().nullable(),
  source_commit: z.string().nullable(),
  knowledge_digest: z.string().regex(/^[0-9a-f]{64}$/),
  skills: z.number().int().nonnegative(),
  knowledge_files: z.number().int().nonnegative(),
  persistence: z.literal("none"),
  external_fetching: z.literal(false),
  prompt_logging: z.literal(false),
  update_model: z.string()
};

const SELECTED_SKILL_SCHEMA = z.object({
  skill_id: z.string(),
  contribution: z.string(),
  reason: z.string(),
  bundle_files: z.number().int().nonnegative(),
  score: z.number()
});

const RUNTIME_DIRECTIVES_OUTPUT_SCHEMA = z.object({
  version: z.string(),
  digest: z.string().regex(/^[0-9a-f]{64}$/),
  content: z.string()
});

const COMPATIBILITY_OUTPUT_SCHEMA = z.object({
  status: z.enum(["compatible", "upgrade_required"]),
  minimum_plugin_version: z.string(),
  same_task_compatible: z.boolean(),
  message: z.string()
});

const START_OUTPUT_SCHEMA = {
  contract_version: z.literal("1.0.0"),
  consultation_id: z.string(),
  knowledge_digest: z.string().regex(/^[0-9a-f]{64}$/),
  plugin_version: z.string(),
  public_release_version: z.string().nullable(),
  runtime_directives: RUNTIME_DIRECTIVES_OUTPUT_SCHEMA,
  selected_skills: z.array(SELECTED_SKILL_SCHEMA),
  matched_routing_fixtures: z.array(z.string()),
  niche_decision_fields: z.array(z.string()),
  compatibility: COMPATIBILITY_OUTPUT_SCHEMA,
  next_step: z.string(),
  extensions: z.record(z.unknown())
};

const LIVE_BUNDLE_OUTPUT_SCHEMA = {
  contract_version: z.literal("1.0.0"),
  consultation_id: z.string(),
  runtime_directives_version: z.string(),
  runtime_directives_digest: z.string().regex(/^[0-9a-f]{64}$/),
  schema_version: z.string(),
  knowledge_digest: z.string().regex(/^[0-9a-f]{64}$/),
  selected_skill_ids: z.array(z.string()),
  files_total: z.number().int().nonnegative(),
  total_characters: z.number().int().nonnegative(),
  page_start_character: z.number().int().nonnegative(),
  page_end_character: z.number().int().nonnegative(),
  chunks: z.array(z.object({
    path: z.string(),
    skill_ids: z.array(z.string()),
    start_character: z.number().int().nonnegative(),
    end_character: z.number().int().nonnegative(),
    content: z.string()
  })),
  next_cursor: z.string().nullable(),
  complete: z.boolean(),
  instruction: z.string(),
  extensions: z.record(z.unknown())
};

function textResult(value) {
  return {
    content: [{ type: "text", text: JSON.stringify(value) }],
    structuredContent: value
  };
}

export function registerLiveConsultantTools(server) {
  server.registerTool(
    "route_consultation",
    {
      title: "Route a Live Consultant request",
      description: "Infer the complete Live Consultant skill stack for one business question. Use this first, then load every selected bundle before answering.",
      inputSchema: {
        query: z.string().min(1).max(12_000).describe("The specific business decision or deliverable requested."),
        business_context: z.string().max(4_000).optional().describe("Only task-specific business facts needed for routing, such as niche, buyer, offer, stage, geography, channel, and constraints. Do not send conversation history, raw transcripts, credentials, personal data, customer lists, or regulated data.")
      },
      outputSchema: ROUTE_OUTPUT_SCHEMA,
      annotations: READ_ONLY_ANNOTATIONS
    },
    async (input) => textResult(await routeConsultation(input))
  );

  server.registerTool(
    "load_knowledge_bundle",
    {
      title: "Load complete Live Consultant knowledge",
      description: "Load the complete files for selected skills in deterministic pages. Keep calling with next_cursor until it is null; do not synthesize from only the first page.",
      inputSchema: {
        skill_ids: z.array(z.string()).min(1).max(24),
        cursor: z.string().optional(),
        page_size_chars: z.number().int().min(2_000).max(30_000).optional()
      },
      outputSchema: BUNDLE_OUTPUT_SCHEMA,
      annotations: READ_ONLY_ANNOTATIONS
    },
    async (input) => textResult(await loadKnowledgeBundle(input))
  );

  server.registerTool(
    "live_consultant_status",
    {
      title: "Check Live Consultant knowledge status",
      description: "Return the deployed knowledge version, digest, file coverage, and privacy-preserving runtime boundaries.",
      inputSchema: {},
      outputSchema: STATUS_OUTPUT_SCHEMA,
      annotations: READ_ONLY_ANNOTATIONS
    },
    async () => textResult(await liveConsultantStatus())
  );

  server.registerTool(
    "start_live_consultation",
    {
      title: "Start a version-pinned Live Consultant consultation",
      description: "Start every v0.6+ consultation here. It returns the current hosted directives, complete niche-specific skill route, compatibility state, and an opaque consultation ID that pins one answer to one knowledge release.",
      inputSchema: {
        query: z.string().min(1).max(12_000).describe("The specific business decision or deliverable requested."),
        business_context: z.string().max(4_000).optional().describe("Only task-specific business facts needed for routing, such as niche, buyer, offer, stage, geography, channel, and constraints. Do not send conversation history, raw transcripts, credentials, personal data, customer lists, or regulated data."),
        client: z.object({
          plugin_version: z.string().max(100).regex(/^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:\+[0-9A-Za-z.-]+)?$/).optional(),
          supported_contract_versions: z.array(z.string().max(100).regex(/^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$/)).min(1).max(8).optional(),
          capabilities: z.array(z.string().max(100)).max(32).optional(),
          extensions: z.record(z.string().max(256)).optional()
        }).strict().optional().describe("Optional non-sensitive compatibility metadata. It is not stored or included in the consultation ID.")
      },
      outputSchema: START_OUTPUT_SCHEMA,
      annotations: READ_ONLY_ANNOTATIONS
    },
    async (input) => textResult(await startLiveConsultation(input))
  );

  server.registerTool(
    "load_live_consultant_bundle",
    {
      title: "Load a version-pinned Live Consultant bundle",
      description: "Load the complete knowledge selected by start_live_consultation in deterministic pages. Keep calling with next_cursor until it is null; if the pinned release is unavailable, start again in the same task rather than mixing versions.",
      inputSchema: {
        consultation_id: z.string().min(1).max(8_192),
        cursor: z.string().max(8_192).optional(),
        page_size_chars: z.number().int().min(2_000).max(30_000).optional()
      },
      outputSchema: LIVE_BUNDLE_OUTPUT_SCHEMA,
      annotations: READ_ONLY_ANNOTATIONS
    },
    async (input) => textResult(await loadLiveConsultantBundle(input))
  );
}
