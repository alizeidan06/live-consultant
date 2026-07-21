# Privacy

Live Consultant includes a read-only hosted MCP service at
`https://live-consultant.sifr.marketing/mcp`. When a user or host invokes one
of its hosted tools, the service receives the tool arguments explicitly sent
with that call so it can route and return the requested knowledge bundle. It
does not require a Live Consultant account, intentionally persist tool
arguments, create learning candidates from calls, or include application-level
advertising or behavioral telemetry.

The preferred v0.6 flow returns an opaque `consultation_id` from
`start_live_consultation` and accepts it in `load_live_consultant_bundle`. This
identifier is an HMAC-authenticated, stateless routing reference rather than an
account, cookie, cross-customer profile, or stored server-side session. It
contains only public contract, knowledge, runtime-directive, and selected-skill
references needed to keep one answer on one reviewed version. It does not
contain the user's request, business context, conversation, credentials, or
personal data. Pagination cursors likewise contain only HMAC-authenticated
consultation and offset references.

The service runs on third-party hosting infrastructure. That infrastructure and
the user's model or MCP host may process operational metadata under their own
privacy and retention terms. Users should not send credentials, raw private
transcripts, customer lists, regulated data, or unnecessary personal data in
hosted tool arguments.

## Hosted data details

- **Categories received:** the requested business outcome, optional minimized
  task-specific business context, optional client compatibility metadata
  (`plugin_version`, supported contract versions, declared capabilities, and
  caller-defined extensions), selected skill IDs, opaque consultation
  identifier, pagination cursor, page size, and ordinary HTTP operational
  metadata processed by the host.
- **Purpose:** route one consultation request, return the selected public
  knowledge and reviewed runtime directives, maintain one-version page
  consistency, check contract compatibility, and report the deployed version.
- **Recipients/processors:** Live Consultant's hosting provider and the user's
  OpenAI, Codex, or other MCP host under those providers' own terms. The service
  does not sell arguments or send them to advertising, analytics, data-broker,
  model-training, or learning-candidate services.
- **Application retention:** none. Live Consultant does not intentionally write
  hosted tool arguments, responses, or identifiers to a database, file, or
  cross-customer memory. Infrastructure security and operational logs, if any,
  follow the hosting provider's terms and settings.
- **User controls:** omit unnecessary context, disconnect or uninstall Live
  Consultant to stop future calls, and report a privacy issue through the
  repository support channel. Do not place secrets or sensitive data in a tool
  argument.

A compatible hosted update can be selected by the next
`start_live_consultation` call in the same v0.6-compatible Codex task. That
behavior does not create persistent memory: every call still carries only its
explicit arguments and stateless identifiers. A consultation remains pinned
to one contract, knowledge, and runtime-directive identity rather than changing
mid-answer.

Project-local learning is off by default. When a user explicitly enables it,
the plugin writes redacted structured candidates and reviewed local rules only
under `.live-consultant/learning/` in the selected project. That directory is
ignored by Git by default. The records remain until the user deletes that
directory. The user can inspect, disable, or delete it at any time.

Preparing a community learning contribution is a second, per-event opt-in. The
tool generates a local sanitized preview and digest. It does not call GitHub,
open an issue, upload a file, or submit anything. The user must review the exact
preview and post it manually if they choose.

Automated filters cannot prove anonymity. Exact human preview is a required
privacy gate, and any later decision change invalidates the old preview. The
local store uses a randomly generated project-local integrity key to sign
candidates, decisions, and the ordered event-ledger head. The key and records
remain inside the ignored learning directory; the key is not an account
credential and is never transmitted.

The bundled plugin runs inside Codex and can work with information and tools
made available in that environment. Any Codex, model-provider, connector,
browser, hosting-provider, or third-party processing is governed by that
product's own configuration and privacy terms.

The included templates explicitly discourage storing secrets and raw private
data. The public release process also scans for common secret signatures and
machine-specific private paths.
