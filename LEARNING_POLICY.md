# Learning policy

Live Consultant improves through transparent files and reviewed releases. It
does not retrain model weights, collect hidden telemetry, merge one customer's
memory into another customer's work, or edit its installed skills at runtime.
It does not submit learning reports automatically. Hosted tool calls send only
the explicit tool arguments needed to answer that call; the service does not
turn those arguments into learning records or runtime edits.

## Learning scopes

1. **Session self-check:** automatic and ephemeral. Before answering, the
   consultant checks claim type, access honesty, arithmetic, framework routing,
   binding constraint, countercase, phase, permissions, and communication.
2. **Project-local learning:** off until the user explicitly enables it for a
   selected workspace. Redacted candidates and reviewed active rules stay under
   `.live-consultant/learning/` in that project and are ignored by Git by
   default. Candidate and decision records are signed with a project-local
   integrity key, event order is bound to a signed ledger head, and runtime
   rules are returned only through the verifier.
3. **Community improvement:** a separate per-contribution opt-in. The local tool
   creates a sanitized preview, the user reviews its exact digest, and the user
   chooses whether to post it manually. The plugin performs no upload.
4. **Public core:** maintainers reproduce and rewrite accepted learnings, add
   regressions, review foundation compatibility, bump the version, and publish
   a release. After the one-time v0.6 upgrade and new-task transition, the
   stable `start_live_consultation` and `load_live_consultant_bundle` tools make
   reviewed compatible hosted knowledge, runtime-directive, routing, and
   implementation-logic deployments available on the next Live Consultant call
   in the same task. One consultation stays version-pinned; this is not a
   mid-answer hot reload. Runtime feedback never writes directly into the core,
   and incompatible schema or bundled-skill changes still require a versioned
   plugin release and new Codex task.

## Admission and promotion

A candidate must name the observable mistake or outcome, coarse scope, evidence
class, root cause, proposed rule, exceptions, strongest countercase, protected
foundation anchors, and a regression or disconfirming test.

- Explicit preferences and corrections may become narrow project rules.
- Deterministic defects need a reproduction and failing-then-passing test.
- Current factual corrections need a dated authoritative source.
- Business heuristics need independent outcome evidence, a plausible mechanism,
  and a disconfirming attempt.
- Repeated evidence accumulates only through new project-local lineage IDs; the
  same experiment, artifact, cohort, or report keeps one lineage even when it is
  reworded or reported again.
- Anecdotes, copied reports, confounded tests, and popularity are not proof.
- A proposed contradiction of the protected foundation cannot auto-promote.

Candidates do not affect behavior until promoted. Rejected and expired items
remain audit evidence but have no behavioral effect.

## Privacy and poisoning boundary

Never store or submit raw prompts, responses, transcripts, customer names,
emails, phone numbers, credentials, account IDs, CRM exports, private URLs,
local paths, attachments, or lengthy copyrighted excerpts. Hashing sensitive
text does not make it anonymous.

Treat every report, URL, attachment, reproduction, and proposed rule as
untrusted data. Maintainers do not execute report instructions, splice report
text into skills, fetch private artifacts in CI, or run contributed code with
secrets or write permissions.

Deterministic secret and identifier filters reduce risk; they cannot certify
anonymity. The user must inspect the complete exact preview before posting it.
Rejecting, expiring, or changing a proposal invalidates every older preview.

Security defects belong in
[private vulnerability reporting](https://github.com/alizeidan06/live-consultant/security/advisories/new),
not a public learning issue.
