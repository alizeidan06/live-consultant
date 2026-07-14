# Meta audit and launch gate

## Baseline

- Account, objective, currency, timezone, date range, attribution view.
- Spend, impressions, reach, frequency, CPM, video hold/retention where
  relevant, clicks, CTR, CPC, landing views, leads, qualified leads, sales,
  refunds, retained customers, net revenue, contribution, CAC, and payback.
- Source reconciliation across Meta, analytics, CRM, checkout, and finance.
- Missing fields and inaccessible surfaces.

## Creative record

```text
creative_id | audience | awareness | angle | hook | proof | format | promise |
destination | changed_variable | spend | leading_metrics | qualified_result |
contribution_result | decision | review_date
```

## Launch gate

- Offer and buyer proof passed.
- Claims ledger reviewed; commercial intent clear.
- Destination works on mobile, matches the ad, and states terms/privacy/support.
- Events tested and deduplicated; finance reconciliation defined.
- Customer data rights, consent, and purpose verified.
- Current Meta policies and special-category rules checked.
- Contribution, maximum CAC, payback, capacity, refund exposure, cash reserve,
  and downside modeled.
- Exact budget, duration, stop conditions, permissions, and rollback printed.
- Owner explicitly approved publishing and spend.

## Decision

`WINNER` requires sufficient evidence of retained contribution or an explicitly
approved leading indicator for the test stage. `KILL` requires a predeclared
threshold or a verified blocker. `LEARN` is valid when data is insufficient but
the test produced a useful next hypothesis. Never keep spending to rescue sunk
cost or to reach an arbitrary platform threshold.
