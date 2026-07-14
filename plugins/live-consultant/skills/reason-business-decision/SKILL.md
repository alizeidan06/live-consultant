---
name: reason-business-decision
description: Analyze difficult business decisions with formal logic, causal reasoning, evidence grading, expected value, sensitivity analysis, reversibility, and adversarial counterarguments. Use when comparing strategies, resolving contradictory advice, deciding whether to build, buy, hire, price, launch, scale, pivot, stop, or invest, or when the user wants a rigorous explanation of what is true, uncertain, irrelevant, and decision-changing.
---

# Reason About a Business Decision

At the start of every invocation, read and apply the mandatory
[Live Consultant communication voice](../founder-business-consultant/references/communication-voice.md).
Use it for every user-facing answer and customer-facing artifact. Simplify the
language, never the reasoning, stakes, specificity, or commercial force.

Turn ambiguity into a decision model without pretending uncertainty has
disappeared.

## Frame precisely

Write one decision sentence with:

- decision owner and deadline;
- mutually exclusive alternatives, including `do nothing`, `delay`, and a
  smaller reversible option when relevant;
- objective and metric of success;
- non-negotiable constraints and approval boundaries;
- time horizon and worst credible downside.

Separate facts, assumptions, predictions, preferences, and constraints. Reject
false dilemmas and overloaded terms before comparing options.

## Build the argument map

Read [logic-protocol.md](references/logic-protocol.md).

1. Define each conclusion and the premises it requires.
2. Check whether evidence supports the premise, the causal link, and the scope.
3. Generate at least one serious alternative explanation.
4. Check base rates, selection effects, survivorship, incentives, measurement,
   missing denominators, and dependence between observations.
5. Distinguish necessary, sufficient, correlated, and merely compatible
   conditions.
6. Identify the crux: the smallest uncertain claim that changes the decision.

## Compute without false precision

Read [decision-math.md](references/decision-math.md). Use ranges when inputs are
uncertain. Show formulas and units. Test conservative, base, and optimistic
cases plus the break-even value.

Do not collapse strategic value into money when the owner values control,
learning, brand, speed, or optionality; model those explicitly and keep the
weights visible.

## Stress-test the choice

- Steelman the best alternative.
- Run a pre-mortem and identify correlated failure modes.
- Check reversibility, time-to-feedback, option value, and cost of delay.
- Define a stop-loss and evidence that would trigger reversal.
- For irreversible or expensive action, present the exact proposed action,
  scope, spend, audience, and rollback before execution.

## Return a decision record

Provide:

1. `Decision` and recommended option.
2. `Why` in a short causal chain.
3. `Evidence` and grade.
4. `Assumptions` ranked by sensitivity.
5. `Countercase` and why it did not win.
6. `Expected outcomes` by scenario.
7. `Crux test` that would most improve the decision.
8. `Reversal condition`, stop-loss, and review date.
9. `Confidence` with an explanation, not a decorative percentage.

If the missing fact is cheap to obtain and decision-changing, obtain it before
recommending. For high-stakes legal, medical, financial, tax, privacy, or
current-policy questions, verify authoritative sources and mark professional
review boundaries.
