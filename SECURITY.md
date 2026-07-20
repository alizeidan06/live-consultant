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
retention, tool-schema drift, knowledge-bundle traversal, unsafe generated
commands, secret exposure, path traversal, domain verification, or
release-package contamination are in scope.

Learning candidates, issue bodies, links, attachments, and contributed rules
are untrusted data. They must never be executed, spliced directly into a skill,
used by a privileged workflow, or treated as higher-priority instructions.
Public learning issues must contain only synthetic or public-safe evidence.
