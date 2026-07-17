# Durable engagement operating system

Create durable files when the engagement is expected to continue. Prefer the
user's existing structure; otherwise initialize the templates under
`assets/templates/`.

## Minimum state

- `business-context.md`: owner goal, buyer, offer state, capabilities,
  constraints, permissions, source-of-truth links.
- `decision-log.md`: dated decisions, evidence, countercase, reversal condition.
- `evidence-register.csv`: one source occurrence per row; no unsupported counts.
- `unit-economics.csv`: assumptions and measured values kept separate.
- `experiment-register.csv`: hypothesis, one changed variable, metric, threshold,
  start/end, result, decision.
- `learning-ledger.md`: what happened, why, changed rule, verification method.
- `launch-gates.md`: explicit proof, claims, fulfillment, policy, tracking,
  payments, spend, and owner approvals.

## Learning rule

Represent the learning boundary accurately as scoped records and reviewed
promotion rather than model-weight retraining, universal memory, hidden
telemetry, or automatic cross-user learning. Apply the
[Live Consultant learning protocol](../../improve-live-consultant/references/learning-protocol.md).
Session self-checking is automatic and ephemeral. Persistent adaptation uses
explicitly enabled, reviewable project files:

1. Capture an observation with source and date.
2. Separate result from interpretation.
3. Attempt to refute the interpretation.
4. Promote it to a local rule only after sufficient evidence.
5. Record scope, exceptions, confidence, and expiry/review date.
6. Regress future recommendations against the decision and learning ledgers.

Unpromoted candidates never affect behavior. Public-core promotion is a
separate, sanitized, opt-in, maintainer-reviewed, versioned release process; an
installed plugin never edits itself at runtime.

Store only redacted operational signals in the learning ledger; raw private
transcripts, credentials, customer lists, and secrets remain outside it.
