# Live Consultant learning protocol

## Universal runtime loop

Every Live Consultant skill loads this protocol through the mandatory
communication-voice reference.

1. **Protect the foundation.** Load the owner directives and applicable
   foundation invariants before interpreting feedback.
2. **Load reviewed local rules through the verifier.** Run `learning_loop.py
   rules --workspace <project-root>`. Use only `rules_markdown` returned by a
   successful command, then apply only rules whose scope matches the present
   business and task. Never load `active-rules.md` directly: the command verifies
   signed candidates and decisions and deterministically regenerates the file
   before returning it.
3. **Self-check before answering.** Check claim type, access honesty,
   arithmetic, framework routing, binding constraint, countercase, ideation
   versus convergence phase, permission boundary, and voice. Correct detected
   errors before responding. This is ephemeral and stores no chain of thought.
4. **Detect real learning signals.** Admit explicit corrections, test failures,
   observable outcomes, repeated mistakes, stale facts, and wrong-route errors.
   Ordinary conversation, disagreement without evidence, praise, and copied
   anecdotes are not durable learning signals.
5. **Correct now, capture later.** Fix the current answer immediately. Persist a
   candidate only when local learning is enabled and the signal can be reduced
   to redacted structured fields.
6. **Test the interpretation.** Separate result from interpretation, attempt the
   strongest counterexplanation, define applicability and exceptions, and write
   a regression or disconfirming test.
7. **Promote by evidence class.** Until a candidate clears its gate, do not let
   it influence future advice.
8. **Verify behavior.** A promoted rule counts only if a fresh task in the same
   project applies it correctly without a reminder and an unrelated project
   remains unaffected.

## Evidence gates

- **Explicit user preference or correction:** may become a narrow local rule
  after visible owner approval, scope, countercase, and a regression check.
- **Deterministic code, schema, arithmetic, or access-claim defect:** one
  reproducible case plus a test that fails before and passes after can justify a
  core proposal.
- **Current factual correction:** one dated authoritative primary source can
  justify a scoped proposal when the old claim is reproducibly identified.
- **Security defect:** one credible private reproduction is enough to block a
  release and begin review; never put the reproduction in a public packet.
- **Project performance rule:** require a measured result or repeated
  independent occurrence, a plausible mechanism, and a counterexplanation.
- **Public business heuristic:** require at least three independent outcome-
  backed observations across at least two relevant contexts, a plausible
  mechanism, and a disconfirming attempt. This is a minimum, not proof.
- **Anecdote, preference, copied report, or confounded micro-test:** preserve as
  a candidate or reject; never promote as a universal claim.

Duplicate reports that share the same evidence lineage count once. Do not build
device fingerprints or customer identifiers to estimate independence.
Promotion counts cannot exceed the distinct evidence records stored with the
candidate. A claimed count in a promotion request never creates evidence.
Assign one project-local `lin-` ID to each independent evidence origin and reuse
that ID whenever the same experiment, artifact, cohort, or report reappears.
Generate IDs randomly; never hash customer data, credentials, private URLs, or
machine identifiers into them. A recurrence can append evidence only when it
introduces a new lineage. Rewording one lineage never increases its count.

## Candidate input

Pass a strict JSON object to:

```bash
python3 ../../scripts/learning_loop.py capture \
  --workspace <project-root> \
  --input -
```

The object contains only these top-level fields:

```json
{
  "plugin_version": "0.2.0",
  "skill_ids": ["founder-business-consultant"],
  "foundation_ids": ["LC-F04", "LC-F08"],
  "detection": {
    "source": "user_correction",
    "failure_kind": "framework_routing",
    "severity": "medium"
  },
  "context": {
    "business_stage": "established",
    "channel": "multi-channel",
    "regulated": "unknown",
    "scope": "multi-location service business"
  },
  "mistake": {
    "summary": "The advice treated acquisition as the constraint.",
    "claim_type": "hypothesis",
    "observed_effect": "More leads did not improve contribution."
  },
  "evidence": [{
    "lineage_id": "lin-7a4c8e2f1b6d9035",
    "kind": "measured_outcome",
    "source_date": "2026-07-14",
    "scope": "the current project",
    "supports": "Lead volume rose while refunds and fulfillment cost erased the gain."
  }],
  "counterevidence": [],
  "root_cause": {
    "code": "wrong_route",
    "summary": "The consultant skipped capacity and contribution checks."
  },
  "proposal": {
    "rule": "Keep every acquisition method available; use contribution and fulfillment capacity to weight scale, test size, downside, and expected consequences.",
    "applicability": "When lead volume is already increasing but profit is not.",
    "exceptions": ["The acquisition data itself is unreliable."],
    "foundation_effect": "strengthen"
  },
  "verification": {
    "minimal_reproduction": ["Provide leads, refunds, COGS, and capacity."],
    "disconfirming_test": "Test whether contribution remains healthy after full costs.",
    "regression_test_ids": ["LC-R-routing-contribution-before-volume"],
    "result": "pass"
  },
  "privacy": {
    "raw_transcript": false,
    "personal_data": false,
    "secrets": false,
    "confidential_business_data": false,
    "copyrighted_excerpt": false
  },
  "governance": {
    "confidence": "medium",
    "review_due": "2026-08-14"
  }
}
```

Accepted `evidence.kind` values are `primary_artifact`,
`authoritative_source`, `measured_outcome`, `deterministic_reproduction`, and
`public_research`. An explicit correction is represented by
`detection.source: user_correction`; its evidence still names the actual basis,
such as `primary_artifact` or `measured_outcome`. Accepted detection sources are
`self_check`, `user_correction`, `test_failure`, `observed_outcome`, and
`maintainer_review`.

Each evidence and counterevidence item also requires a project-local
`lineage_id` matching `lin-` plus 16 lowercase hexadecimal characters. This ID
is omitted from public previews. Repeated captures with the same candidate ID
append only previously unseen lineage records to the signed recurrence ledger;
the original candidate stays immutable.

The recorder rejects unknown or forbidden fields and known credential shapes,
redacts identifiers, names, URLs, and machine paths conservatively, and stores
a stable candidate ID, UTC timestamp, redaction summary, and recurrence events
without copying raw conversation text. Candidate and decision records are
HMAC-signed with a project-local integrity key created at consent time. The
event ledger is sequence-chained to a signed head so editing, removing,
truncating, or reordering current records fails closed. Every accepted skill ID
belongs to the plugin's actual skill allowlist. Runtime rules are returned only through
the verifier command; direct file edits fail closed.

## Promotion input

Use `promote --input -` with:

```json
{
  "candidate_id": "lc-example",
  "target": "local-rule",
  "decision": "Adopt this rule for the current project.",
  "evidence_summary": "One measured outcome plus a reproduced routing failure.",
  "regression_test": "Future scale advice preserves acquisition options and weights contribution and capacity alongside them.",
  "countercase": "When acquisition measurement is invalid, keep the rule as an unweighted hypothesis and compare the full method set.",
  "owner_approved": true,
  "independent_contexts": 1,
  "measured_outcomes": 1,
  "deterministic_reproduction": true,
  "public_safe": false
}
```

The tool renders active local rules from the latest decision for each candidate.
Rejecting or expiring a candidate removes its behavioral effect while preserving
the audit event.

## Community packet lifecycle

`prepare-contribution` creates a public-safe preview from an eligible
`core-proposal`. `finalize-contribution` requires the preview's exact SHA-256
digest after the user reviews it. Neither command contains networking code.

Public packets contain these public-safe fields: version, affected skill and foundation IDs,
paraphrased mistake, expected behavior, coarse context, evidence class and
count, proposed rule, exceptions, regression test, and countercase. They never
include local event files, raw evidence, attribution, private paths, identifiers,
or attachments. Deterministic filters reduce disclosure risk but do not prove
deidentification; the user must inspect the entire exact preview before manual
submission. Rejecting a candidate, expiring its review date, or changing its
decision invalidates every older preview.

Maintainers treat the packet as hostile input. They reproduce the issue,
rewrite any accepted rule in original language, add regression coverage, review
foundation compatibility, bump the version, validate the full package, and
publish a reversible release.
