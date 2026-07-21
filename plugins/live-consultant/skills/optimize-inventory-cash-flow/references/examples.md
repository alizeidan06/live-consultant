# Inventory and cash-flow examples

All numbers are hypothetical and shown only to demonstrate the arithmetic.

## Landed unit contribution

```text
supplier goods:                 50,000
freight/insurance:               6,000
duty/brokerage/inland/handling:  4,000
usable received units:           5,000
landed unit cost:                60,000 / 5,000 = 12.00

expected net selling price:      21.00
commission/delivery/fees/reserve: 3.00
landed contribution per unit:     6.00
```

At 5,000 units, the shipment contributes 30,000 before fixed overhead and tax
if every assumption holds. Show downside cases for price, returns, damage, and
sell-through before purchasing.

## Inventory velocity and GMROI

For a 90-day period with 180,000 COGS, 150,000 average inventory at cost, and
72,000 gross margin:

```text
period turns = 180,000 / 150,000 = 1.20
annualized turns = 1.20 × 365 / 90 = 4.87
DIO = 150,000 / 180,000 × 90 = 75 days
GMROI = 72,000 / 150,000 = 0.48 for the period
```

## Cash-conversion cycle

If DIO is 75 days, DSO is 32, and DPO is 28:

```text
cash conversion cycle = 75 + 32 - 28 = 79 days
```

The business finances roughly 79 days between cash committed and cash
recovered under these assumptions.

## Container constraint

```text
payload utilization = 26,000 / 27,000 = 96.3%
cube utilization = 40 / 67 = 59.7%
```

Weight is closer to its limit. The unused cube does not authorize more cargo.
Test lighter compatible items only after axle, route, handling, customs,
compatibility, demand, and cash contribution checks.

## Commitment-weighted purchase decision

```text
12 verbal requests
6 sample requests
4 qualified quotes
2 signed purchase orders
1 deposit
```

Do not call this 12 customers. Model the committed quantity, cancellation
rights, buyer authority, deposit coverage, and downside if only the strongest
commitment converts.

## Thirteen-week row

```text
week 4 opening cash:       48,000
receipts/deposits:         22,000
supplier/freight outflow: -31,000
payroll/rent/other:       -18,000
week 4 ending cash:        21,000
cash floor:                25,000
```

The plan breaches the floor in week 4. The decision must happen before week 4:
accelerate real collections, delay or resize the purchase, change terms, or
approve financing. A hoped-for sale is not a receipt.
