# Audit finding schema

```text
ID:
Severity: BLOCKING | MATERIAL | POLISH
Surface:
Claim:
Evidence and locator:
Evidence status: verified | reported | inferred
Scope and date range:
Business impact:
Strongest countercase:
Reproduction or calculation:
Smallest concrete fix:
Verification after fix:
Owner approval required:
```

Rules:

- No evidence means no finding; convert it to a data request or test.
- Include the denominator, cohort, time window, currency, and attribution source
  for every metric.
- Recompute totals; do not trust dashboard labels or author confidence.
- State what was checked and found clean.
- Group repeated instances under one root-cause finding and sweep the class.
- Keep recommendations testable: one change, one metric, one threshold, one
  review point.
