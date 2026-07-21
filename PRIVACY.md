# Privacy

Live Consultant includes a read-only hosted MCP service at
`https://live-consultant.sifr.marketing/mcp`. When a user or host invokes one
of its hosted tools, the service receives the tool arguments explicitly sent
with that call so it can route and return the requested knowledge bundle. It
does not require a Live Consultant account, intentionally persist tool
arguments, create learning candidates from calls, or include application-level
advertising or behavioral telemetry.

The service runs on third-party hosting infrastructure. That infrastructure and
the user's model or MCP host may process operational metadata under their own
privacy and retention terms. Users should not send credentials, raw private
transcripts, customer lists, regulated data, or unnecessary personal data in
hosted tool arguments.

## Hosted data details

- **Categories received:** the requested business outcome, optional minimized
  task-specific business context, selected skill IDs, pagination cursor, page
  size, and ordinary HTTP operational metadata processed by the host.
- **Purpose:** route one consultation request, return the selected public
  knowledge, maintain page consistency, and report the deployed version.
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
