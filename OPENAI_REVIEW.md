# OpenAI reviewer packet

This packet is the copy-ready review plan for the hosted Live Consultant app.
The production endpoint is `https://live-consultant.sifr.marketing/mcp`.

## Data and network declaration

- The app has no embedded UI and requests no browser content-security-policy
  domains.
- `connect_domains`: `[]`
- `resource_domains`: `[]`
- Hosted tools are public, read-only, unauthenticated, non-destructive, and do
  not call external services.
- The app intentionally persists no tool arguments or responses.
- `consultation_id` and pagination cursors are HMAC-authenticated, stateless routing
  references, not customer accounts or server-side sessions. They contain no
  request text, business context, transcript, credential, or personal data.
- Support: <https://github.com/alizeidan06/live-consultant/issues>
- Privacy: <https://github.com/alizeidan06/live-consultant/blob/main/PRIVACY.md>
- Terms: <https://github.com/alizeidan06/live-consultant/blob/main/TERMS.md>

## Five positive reviewer tests

1. **Stable consultation start:** Call `start_live_consultation` with a request
   to audit lead generation for a Toronto HVAC business and only minimized
   business context. Optionally provide `client.plugin_version`,
   `client.supported_contract_versions`, `client.capabilities`, and
   `client.extensions`. Expect a contract version, opaque `consultation_id`,
   knowledge identity, versioned runtime directives, non-empty complete skill
   stack, niche-decision fields, and explicit compatibility result.
2. **Complete version-pinned load:** Call `load_live_consultant_bundle` with
   that `consultation_id` and a 2,000-character page, then follow every
   `next_cursor`. Expect `complete: true` only on the final page, no repeated or
   missing character range, and the same consultation, contract, knowledge,
   and runtime-directive identity on every page.
3. **Cross-skill assembly:** Start a consultation from a minimized importer
   meeting synopsis involving urgent cash, slow inventory, weak product-demand
   evidence, and automation. Expect meeting analysis, inventory cash flow,
   audit, decision, operations, and demand/pricing skills where each has a distinct
   contribution, then expect deterministic file ordering, file-to-skill
   associations, and one shared case copy when bundles overlap.
4. **Legacy compatibility:** Call `route_consultation`, then
   `load_knowledge_bundle`, with a valid request. Expect their established
   schemas and response shapes to remain usable for an older client while the
   new tools are preferred by v0.6 clients.
5. **Deployment status:** Call `live_consultant_status`. Expect 26 skills, a
   64-character knowledge digest, no persistence, no external fetching, and no
   prompt logging.

## Three negative reviewer tests

1. **Altered consultation identifier:** Change one character in a
   `consultation_id`. Expect a closed validation failure with no bundle data and
   no server-side session lookup.
2. **Stale or altered cursor:** Change a cursor, combine it with a different
   consultation, or use an identity that the deployment cannot serve. Expect a
   closed failure requiring a new `start_live_consultation` call; no response
   may combine two knowledge or runtime-directive versions.
3. **Oversized or inappropriate routing context:** Send more than 4,000
   characters in `business_context` to `start_live_consultation`. Expect input
   rejection. The field
   description also tells clients not to send transcripts, credentials,
   personal data, customer lists, or regulated data.

## Submission notes

- Recommended availability: every country and region where OpenAI permits
  third-party business apps, with no claim of regulated professional advice.
- The submission must use the real OpenAI-issued app ID and the production MCP
  scan. Never substitute a placeholder ID.
- Installing v0.7.0 requires one new Codex task to discover its two new local
  skill entrypoints; v0.6 first established the permanent tool schemas.
  Thereafter, reviewed compatible hosted updates begin on the next Live
  Consultant call in the same task. The service does not claim mid-answer hot
  reloads, and incompatible schema or bundled changes still use a versioned
  plugin release.
- Production stores a strong `LIVE_CONSULTANT_TOKEN_SECRET` only in Deno
  environment settings. It is never committed or returned. Missing or short
  configuration makes `/healthz` and the v0.6 tools fail closed.
- Final identity, domain, policy, and release attestations remain owner actions
  in the OpenAI portal.
