# Privacy

Live Consultant's bundled code does not operate a remote service, collect
telemetry, create an account, or transmit data to a publisher-controlled server.

Project-local learning is off by default. When a user explicitly enables it,
the plugin writes redacted structured candidates and reviewed local rules only
under `.live-consultant/learning/` in the selected project. That directory is
ignored by Git by default. The user can inspect, disable, or delete it.

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

The plugin runs inside Codex and can work with information and tools made
available in that environment. Any Codex, model-provider, connector, browser,
or third-party tool processing is governed by that product's own configuration
and privacy terms. Users should review the tools they enable and avoid placing
credentials, raw private transcripts, customer lists, or unnecessary personal
data into generated workspaces or repositories.

The included templates explicitly discourage storing secrets and raw private
data. The public release process also scans for common secret signatures and
machine-specific private paths.
