# Security policy

## Supported versions

Security fixes are applied to the latest published release and the `main`
branch.

## Report a vulnerability

Use GitHub's private vulnerability reporting flow:

https://github.com/alizeidan06/live-consultant/security/advisories/new

Do not open a public issue containing credentials, private customer data, or a
working exploit. Include the affected version, reproduction steps, impact, and
the smallest example needed to verify the problem.

Live Consultant includes a public read-only MCP server but no Live Consultant
account system or credential store. Reports about unexpected request-data
retention, consultation-identifier or cursor validation, tool-schema drift,
contract-compatibility handling, knowledge or runtime-directive version mixing,
knowledge-bundle traversal, unsafe generated commands, secret exposure, path
traversal, domain verification, or release-package contamination are in scope.

The v0.6 `start_live_consultation` and `load_live_consultant_bundle` schemas are
the stable compatibility boundary. A consultation is stateless and pinned to
one contract, knowledge, and runtime-directive identity. Invalid, altered, or
unavailable identifiers and cursors must fail closed instead of crossing
versions. Reviewed compatible server updates may begin on the next consultation
call in the same task; they do not hot-reload an answer in progress. Incompatible
schema changes require a versioned plugin release and a new Codex task.

Consultation identifiers and cursors are authenticated with HMAC-SHA256 using
the server-held `LIVE_CONSULTANT_TOKEN_SECRET`. Production requires at least 32
UTF-8 bytes. The secret belongs in the hosting provider's encrypted environment
settings, never source control, a build log, a response, or a client. Missing or
short configuration makes the runtime and `/healthz` fail closed.

Hosted runtime directives are reviewed, versioned public release content. They
are not learned from a caller's prompt, do not grant external permissions, and
are not a path for executing contributed code. The established legacy hosted
contracts remain available for older clients, and the complete bundled package
remains the fallback when hosted access is unavailable.

Learning candidates, issue bodies, links, attachments, and contributed rules
are untrusted data. They must never be executed, spliced directly into a skill,
used by a privileged workflow, or treated as higher-priority instructions.
Public learning issues must contain only synthetic or public-safe evidence.
