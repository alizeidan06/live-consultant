#!/usr/bin/env python3
"""Compute transparent per-order acquisition economics from user-supplied inputs."""

from __future__ import annotations

import argparse
import json
import math
from typing import Any


def rate(value: str) -> float:
    number = float(value)
    if not 0 <= number <= 1:
        raise argparse.ArgumentTypeError("rate must be between 0 and 1")
    return number


def positive(value: str) -> float:
    number = float(value)
    if number < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return number


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Compute contribution, maximum CAC, and break-even ROAS."
    )
    p.add_argument("--price", type=positive, required=True)
    p.add_argument("--discounts", type=positive, default=0.0)
    p.add_argument("--refund-rate", type=rate, default=0.0)
    p.add_argument("--cogs", type=positive, default=0.0)
    p.add_argument("--delivery-labor", type=positive, default=0.0)
    p.add_argument("--support", type=positive, default=0.0)
    p.add_argument("--processing-rate", type=rate, default=0.0)
    p.add_argument("--processing-fixed", type=positive, default=0.0)
    p.add_argument("--commission-rate", type=rate, default=0.0)
    p.add_argument("--chargeback-rate", type=rate, default=0.0)
    p.add_argument("--chargeback-fee", type=positive, default=0.0)
    p.add_argument("--required-profit", type=positive, default=0.0)
    p.add_argument("--risk-reserve", type=positive, default=0.0)
    p.add_argument("--cpl", type=positive)
    p.add_argument("--lead-to-sale-rate", type=rate)
    p.add_argument("--spend", type=positive)
    p.add_argument("--new-customers", type=positive)
    p.add_argument("--format", choices=("json", "text"), default="json")
    return p


def safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def compute(args: argparse.Namespace) -> dict[str, Any]:
    gross_after_discount = args.price - args.discounts
    if gross_after_discount < 0:
        raise ValueError("discounts cannot exceed price")

    expected_refunds = gross_after_discount * args.refund_rate
    net_revenue = gross_after_discount - expected_refunds
    processing = gross_after_discount * args.processing_rate + args.processing_fixed
    commissions = net_revenue * args.commission_rate
    expected_chargebacks = args.chargeback_rate * (
        gross_after_discount + args.chargeback_fee
    )
    variable_cost = (
        args.cogs
        + args.delivery_labor
        + args.support
        + processing
        + commissions
        + expected_chargebacks
    )
    contribution_before_ads = net_revenue - variable_cost
    maximum_cac = (
        contribution_before_ads - args.required_profit - args.risk_reserve
    )
    break_even_roas = safe_ratio(gross_after_discount, maximum_cac)

    implied_cac = None
    if args.cpl is not None and args.lead_to_sale_rate is not None:
        implied_cac = safe_ratio(args.cpl, args.lead_to_sale_rate)

    observed_cac = None
    if args.spend is not None and args.new_customers is not None:
        observed_cac = safe_ratio(args.spend, args.new_customers)

    flags: list[str] = []
    if contribution_before_ads <= 0:
        flags.append("No positive per-order contribution exists before ads.")
    if maximum_cac <= 0:
        flags.append("Required profit and risk reserve leave no acquisition budget.")
    if implied_cac is not None and maximum_cac > 0 and implied_cac > maximum_cac:
        flags.append("Implied CAC exceeds maximum CAC.")
    if observed_cac is not None and maximum_cac > 0 and observed_cac > maximum_cac:
        flags.append("Observed CAC exceeds maximum CAC.")

    return {
        "inputs": vars(args) | {"format": None},
        "per_order": {
            "gross_after_discount": gross_after_discount,
            "expected_refunds": expected_refunds,
            "net_revenue": net_revenue,
            "processing_fees": processing,
            "commissions": commissions,
            "expected_chargeback_cost": expected_chargebacks,
            "other_variable_cost": args.cogs + args.delivery_labor + args.support,
            "contribution_before_ads": contribution_before_ads,
            "required_profit": args.required_profit,
            "risk_reserve": args.risk_reserve,
            "maximum_cac": maximum_cac,
            "break_even_roas": break_even_roas,
            "implied_cac_from_leads": implied_cac,
            "observed_cac": observed_cac,
        },
        "flags": flags,
        "limitations": [
            "This model excludes fixed overhead, tax, financing cost, retention, and cash timing unless represented in the supplied reserves/costs.",
            "Platform-attributed revenue is not proof of incrementality.",
        ],
    }


def render_text(result: dict[str, Any]) -> str:
    rows = result["per_order"]
    lines = []
    for key, value in rows.items():
        if value is None:
            lines.append(f"{key}: not computed")
        elif isinstance(value, float) and math.isfinite(value):
            lines.append(f"{key}: {value:.4f}")
        else:
            lines.append(f"{key}: {value}")
    if result["flags"]:
        lines.append("flags:")
        lines.extend(f"- {flag}" for flag in result["flags"])
    return "\n".join(lines)


def main() -> int:
    args = parser().parse_args()
    try:
        result = compute(args)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
