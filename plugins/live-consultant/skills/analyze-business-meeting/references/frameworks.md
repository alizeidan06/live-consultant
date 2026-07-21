# Business meeting evidence framework

## Source quality card

Record the artifact type, date, duration or page span, generation method,
available speaker map, transcription quality, language issues, overlaps,
missing sections, and business-relevant coverage. A transcript is a lossy
record. A speaker map can raise or lower attribution confidence but does not
repair inaudible words or turn opinions into facts.

## Four-axis statement ledger

Keep these dimensions independent:

| Dimension | Values | Question answered |
|---|---|---|
| Attribution | `HIGH`, `MEDIUM`, `LOW`, `UNATTRIBUTED` | Who likely said it? |
| Evidence status | `verified`, `reported`, `inferred`, `unsupported`, `unknown` | How well is it established? |
| Claim type | `observation`, `estimate`, `preference`, `constraint`, `forecast`, `causal claim` | What kind of assertion is it? |
| Meeting function | `statement`, `question`, `diagnosis`, `proposal`, `decision`, `commitment`, `objection` | What role did it play in the meeting? |

High attribution does not imply high truth confidence. A clearly identified
owner can still report an approximate or unverified number.

## Objective lock and drift test

```text
owner outcome | urgency | horizon | metric | survival floor |
decision owner | non-negotiables | reversal condition
```

Capture the lock when the owner first states the problem. Compare it with the
dominant discussion and closing recap. Flag drift when the proposed work no
longer addresses the locked horizon or metric. Do not forbid the long-term
idea; place it in the durable lane and restore an immediate lane.

## Claim and contradiction register

```text
claim_id | normalized claim | attribution confidence | evidence status |
claim type | meeting function | source locator | supporting evidence |
contradiction | decision impact | next verification
```

Common contradictions include urgent cash versus long-horizon brand work,
“no demand” versus “sales process unknown,” verbal demand versus cancelled
purchases, and “AI will solve it” versus no reliable source data.

## Decision-state ladder

```text
DISCUSSED → PROPOSED → DECIDED → ASSIGNED → COMPLETED
```

Do not skip a state. A polite agreement, brainstorm, or closing summary is not
automatically a decision. `ASSIGNED` requires an owner and due date.
`COMPLETED` requires a verifiable artifact or outcome.

## Issue-tree route

Group material issues under demand, buyer/segment, offer, price, inventory,
cash, acquisition, sales, funnel, delivery, operations, data, people, and
external constraints. Then select every skill with a distinct contribution.
The meeting skill owns extraction and meeting quality; domain skills own the
substantive diagnosis.

## Minimum data pack

Replace “send everything” with a decision-matched request:

```text
field | exact definition | period | grain | source | owner | format |
why it changes the decision | acceptable fallback
```

Request the fewest fields that can separate the leading diagnosis from its
countercase. Data volume is not decision quality.

## Deterministic action close

Every action contains:

```text
action | owner | due date | input | deliverable | success metric |
dependency | next decision | escalation if missed
```

If the meeting did not assign a field, write `UNASSIGNED` or `UNKNOWN`. Never
invent accountability to make the brief look complete.
