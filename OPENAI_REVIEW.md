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
- Support: <https://github.com/alizeidan06/live-consultant/issues>
- Privacy: <https://github.com/alizeidan06/live-consultant/blob/main/PRIVACY.md>
- Terms: <https://github.com/alizeidan06/live-consultant/blob/main/TERMS.md>

## Five positive reviewer tests

1. **Niche routing:** Call `route_consultation` with a request to audit lead
   generation for a Toronto HVAC business. Expect a non-empty complete skill
   stack and the niche-decision fields.
2. **Offer and funnel routing:** Route a request to improve a proven dental
   implant offer and its funnel. Expect offer, funnel, buyer, and sales-related
   skills where each has a distinct contribution.
3. **Complete pagination:** Call `load_knowledge_bundle` for
   `sell-like-crazy` with a 2,000-character page, then follow every
   `next_cursor`. Expect `complete: true` only on the final page and no repeated
   or missing character range.
4. **Cross-skill bundle:** Load `audit-business` and
   `reason-business-decision` together. Expect deterministic file ordering,
   file-to-skill associations, and one shared file copy when bundles overlap.
5. **Deployment status:** Call `live_consultant_status`. Expect 24 skills, a
   64-character knowledge digest, no persistence, no external fetching, and no
   prompt logging.

## Three negative reviewer tests

1. **Unknown skill:** Call `load_knowledge_bundle` with a nonexistent skill ID.
   Expect a validation error and no data.
2. **Stale or altered cursor:** Change a cursor or reuse one from another
   knowledge digest. Expect a closed failure requiring a restart from the first
   page.
3. **Oversized or inappropriate routing context:** Send more than 4,000
   characters in `business_context`. Expect input rejection. The field
   description also tells clients not to send transcripts, credentials,
   personal data, customer lists, or regulated data.

## Submission notes

- Recommended availability: every country and region where OpenAI permits
  third-party business apps, with no claim of regulated professional advice.
- The submission must use the real OpenAI-issued app ID and the production MCP
  scan. Never substitute a placeholder ID.
- Final identity, domain, policy, and release attestations remain owner actions
  in the OpenAI portal.
