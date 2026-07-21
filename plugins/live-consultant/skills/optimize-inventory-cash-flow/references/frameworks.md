# Inventory and cash-conversion framework

## Evidence contract

For every calculation record the period, days in period, currency, unit, SKU
or segment grain, accounting source, snapshot method, freshness, and evidence
status. Do not mix units, tax treatment, cash and accrual values, or retail and
wholesale prices silently.

## Revenue and landed contribution

```text
expected net revenue
= invoiced revenue
- discounts
- expected returns, rebates, credits, and chargebacks

total landed cost
= supplier product cost
+ origin handling
+ freight and insurance
+ duties and tariffs
+ customs and brokerage
+ inland transport
+ inspection and handling
+ other shipment-specific variable cost

landed unit cost = total landed cost / usable received units

landed contribution per unit
= expected net selling price
- landed unit cost
- sales commission
- variable delivery and fulfillment
- payment and marketplace fees
- expected warranty, return, bad-debt, and financing cost
```

Allocate shared shipment costs with an explicit driver such as weight, cube,
units, value, or handling complexity. Show how the result changes under a
reasonable alternative driver when allocation changes the decision.

## Inventory velocity

```text
average inventory cost = average of reliable period snapshots
period turns = period COGS / average inventory cost
annualized turns = period turns × 365 / period days
DIO = average inventory cost / period COGS × period days
sell-through = units sold / (beginning units + received units)
GMROI = gross margin dollars / average inventory at cost
```

If the denominator is zero, unreliable, or negative, return `NOT COMPUTABLE`.
Do not substitute revenue for COGS or ending inventory for average inventory
without labeling the approximation.

Age inventory by both units and cost: current, slow, at-risk, dead, damaged,
committed, and unavailable. Define thresholds from the category's real reorder
and sales cycle rather than importing universal day bands.

## Working capital and cash-conversion cycle

```text
DSO = average receivables / net credit sales × period days
DPO = average payables / credit purchases × period days
cash conversion cycle = DIO + DSO - DPO
```

Compute cash timing separately from accounting profit. A profitable shipment
can still create a cash crisis when deposits, freight, duties, inventory hold,
credit terms, and collections happen in the wrong sequence.

## Container and freight utilization

```text
payload utilization = cargo weight / route-legal usable payload
cube utilization = cargo volume / usable internal cube
```

Evaluate both. The binding limit is whichever relevant constraint reaches its
safe or legal maximum first. Empty cube is not automatically recoverable when
weight, axle distribution, route, stacking, compatibility, handling, damage,
customs, supplier minimums, or demand binds. A filler SKU improves economics
only if its incremental contribution and cash timing beat its risk and handling
cost.

## Segment and channel cash economics

For each segment calculate:

```text
net price | units/order | frequency | landed contribution | commission |
CAC or sales cost | credit days | service/returns | default risk |
cash receipt date | repeat rate | inventory commitment
```

Revenue share is not contribution share. A channel with a lower price can be
more valuable if it turns inventory and cash faster; a higher-margin channel
can still be worse when acquisition, service, credit, or returns consume the
gain.

## Thirteen-week cash forecast

For each week:

```text
opening cash
+ collected receivables
+ cash sales and deposits
+ financing or owner contribution
- supplier payments
- freight, duty, and inbound cost
- payroll and commissions
- rent, debt, tax, refunds, and other committed outflows
= ending cash
```

Maintain expected, downside, and committed views. Separate amount from timing.
Name the first week below the cash floor and the decision required before that
week. Do not count an open quote or verbal promise as a receipt.

## Cash-release option set

Keep all options available, then compare contribution, speed, cash collected,
brand/channel effect, operational load, reversibility, and downside:

- collect receivables and deposits;
- convert open quotes and commitments;
- sell, bundle, reprice, liquidate, return, transfer, or repurpose aging stock;
- pause, reduce, substitute, consolidate, or reschedule purchases;
- renegotiate deposits, payment terms, freight, or minimums;
- pre-sell or secure enforceable commitments before import;
- protect a productive channel while testing a new one;
- repair the sales/funnel step preventing tactile or complex product purchase.
