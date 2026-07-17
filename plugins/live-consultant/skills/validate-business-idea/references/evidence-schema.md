# Evidence schema

Use one row per source occurrence.

```csv
candidate_id,buyer_role,trigger,problem_scope,source_type,source_url_or_path,locator,observed_at,event_date,access_state,exact_buyer,material_consequence,completed_spend,current_behavior,price_currency,repeat_cadence,alternative,value_gap,disconfirming_signal,commercial_source,redaction_status,coder_rationale
```

Record buyer identity, recency, payment, currency, recurrence, consequence, and
failed alternatives as `SUPPORTED` only when the source provides that evidence;
otherwise retain `UNKNOWN`.

Grade evidence:

- `A`: direct transaction, signed commitment, observed behavior, or verified
  first-party metric in the exact scope.
- `B`: exact-buyer primary statement with provenance and concrete behavior.
- `C`: credible category context, competitor checkout/terms, or vendor supply.
- `D`: secondary summary, anecdote, search volume, or unverified claim.

Category/supply evidence cannot be counted as exact-buyer demand. Commercial
sources may establish price, scope, and terms but need independent demand
evidence.
