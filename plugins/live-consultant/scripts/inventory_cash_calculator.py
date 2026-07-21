#!/usr/bin/env python3
"""Compute transparent inventory, landed-cost, and cash-conversion metrics."""

from __future__ import annotations

import argparse
import json
import math
from typing import Any


def finite_number(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise argparse.ArgumentTypeError("value must be a finite number")
    return number


def non_negative(value: str) -> float:
    number = finite_number(value)
    if number < 0:
        raise argparse.ArgumentTypeError("value must be a finite non-negative number")
    return number


def positive(value: str) -> float:
    number = non_negative(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return number


def rate(value: str) -> float:
    number = non_negative(value)
    if number > 1:
        raise argparse.ArgumentTypeError("rate must be between 0 and 1")
    return number


def thirteen_values(value: str) -> list[float]:
    try:
        values = [float(item.strip()) for item in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "weekly values must be comma-separated numbers"
        ) from exc
    if len(values) != 13:
        raise argparse.ArgumentTypeError("weekly values must contain exactly 13 numbers")
    if any(not math.isfinite(item) or item < 0 for item in values):
        raise argparse.ArgumentTypeError(
            "weekly values must be finite non-negative numbers"
        )
    return values


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Compute landed contribution, inventory velocity, cash-conversion "
            "cycle, container utilization, and an optional 13-week cash forecast."
        )
    )
    p.add_argument("--supplier-cost", type=non_negative)
    p.add_argument("--origin-handling", type=non_negative)
    p.add_argument("--freight-insurance", type=non_negative)
    p.add_argument("--duties-tariffs", type=non_negative)
    p.add_argument("--customs-brokerage", type=non_negative)
    p.add_argument("--inland-transport", type=non_negative)
    p.add_argument("--inspection-handling", type=non_negative)
    p.add_argument("--other-shipment-cost", type=non_negative)
    p.add_argument("--usable-units", type=positive)
    p.add_argument("--selling-price", type=non_negative)
    p.add_argument("--discount-per-unit", type=non_negative)
    p.add_argument("--return-rate", type=rate)
    p.add_argument("--commission-per-unit", type=non_negative)
    p.add_argument("--delivery-per-unit", type=non_negative)
    p.add_argument("--fees-per-unit", type=non_negative)
    p.add_argument("--warranty-bad-debt-per-unit", type=non_negative)
    p.add_argument("--financing-per-unit", type=non_negative)

    p.add_argument("--period-days", type=positive)
    p.add_argument("--period-cogs", type=non_negative)
    p.add_argument("--average-inventory-cost", type=non_negative)
    p.add_argument("--gross-margin-dollars", type=finite_number)
    p.add_argument("--units-sold", type=non_negative)
    p.add_argument("--beginning-units", type=non_negative)
    p.add_argument("--received-units", type=non_negative)
    p.add_argument("--average-receivables", type=non_negative)
    p.add_argument("--net-credit-sales", type=non_negative)
    p.add_argument("--average-payables", type=non_negative)
    p.add_argument("--credit-purchases", type=non_negative)

    p.add_argument("--cargo-weight", type=non_negative)
    p.add_argument("--usable-payload", type=positive)
    p.add_argument("--cargo-volume", type=non_negative)
    p.add_argument("--usable-cube", type=positive)

    p.add_argument("--opening-cash", type=non_negative)
    p.add_argument("--weekly-receipts", type=thirteen_values)
    p.add_argument("--weekly-outflows", type=thirteen_values)
    p.add_argument("--cash-floor", type=non_negative, default=0.0)
    p.add_argument("--format", choices=("json", "text"), default="json")
    return p


def safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def complete_group(
    values: dict[str, float | list[float] | None],
    names: tuple[str, ...],
    label: str,
    *,
    trigger_names: tuple[str, ...] | None = None,
) -> None:
    triggers = trigger_names or names
    if not any(values[name] is not None for name in triggers):
        return
    present = [values[name] is not None for name in names]
    if not all(present):
        missing = ", ".join(name for name in names if values[name] is None)
        raise ValueError(f"{label} requires all related inputs; missing: {missing}")


def compute(args: argparse.Namespace) -> dict[str, Any]:
    values = vars(args)
    landed_inputs = (
        "supplier_cost",
        "origin_handling",
        "freight_insurance",
        "duties_tariffs",
        "customs_brokerage",
        "inland_transport",
        "inspection_handling",
        "other_shipment_cost",
        "usable_units",
        "selling_price",
        "discount_per_unit",
        "return_rate",
        "commission_per_unit",
        "delivery_per_unit",
        "fees_per_unit",
        "warranty_bad_debt_per_unit",
        "financing_per_unit",
    )
    complete_group(
        values,
        ("supplier_cost", "usable_units", "selling_price"),
        "landed economics",
        trigger_names=landed_inputs,
    )
    complete_group(
        values,
        ("period_days", "period_cogs", "average_inventory_cost"),
        "inventory velocity",
        trigger_names=("period_cogs",),
    )
    complete_group(
        values,
        ("gross_margin_dollars", "average_inventory_cost"),
        "GMROI",
        trigger_names=("gross_margin_dollars",),
    )
    complete_group(
        values,
        ("units_sold", "beginning_units", "received_units"),
        "sell-through",
    )
    complete_group(
        values,
        ("average_receivables", "net_credit_sales", "period_days"),
        "DSO",
        trigger_names=("average_receivables", "net_credit_sales"),
    )
    complete_group(
        values,
        ("average_payables", "credit_purchases", "period_days"),
        "DPO",
        trigger_names=("average_payables", "credit_purchases"),
    )
    complete_group(values, ("cargo_weight", "usable_payload"), "payload utilization")
    complete_group(values, ("cargo_volume", "usable_cube"), "cube utilization")
    complete_group(
        values,
        ("opening_cash", "weekly_receipts", "weekly_outflows"),
        "13-week cash forecast",
    )

    if not any(
        values[name] is not None
        for name in (
            *landed_inputs,
            "period_cogs",
            "gross_margin_dollars",
            "units_sold",
            "average_receivables",
            "average_payables",
            "cargo_weight",
            "cargo_volume",
            "opening_cash",
        )
    ):
        raise ValueError("provide at least one complete metric group")

    total_landed_cost = None
    landed_unit_cost = None
    expected_net_price = None
    other_variable_cost = None
    landed_contribution_per_unit = None
    full_sell_through_contribution_potential = None
    if args.supplier_cost is not None:
        total_landed_cost = sum(
            value or 0.0
            for value in (
                args.supplier_cost,
                args.origin_handling,
                args.freight_insurance,
                args.duties_tariffs,
                args.customs_brokerage,
                args.inland_transport,
                args.inspection_handling,
                args.other_shipment_cost,
            )
        )
        landed_unit_cost = total_landed_cost / args.usable_units
        gross_after_discount = args.selling_price - (args.discount_per_unit or 0.0)
        if gross_after_discount < 0:
            raise ValueError("discount per unit cannot exceed selling price")
        expected_return_cost = gross_after_discount * (args.return_rate or 0.0)
        expected_net_price = gross_after_discount - expected_return_cost
        other_variable_cost = sum(
            value or 0.0
            for value in (
                args.commission_per_unit,
                args.delivery_per_unit,
                args.fees_per_unit,
                args.warranty_bad_debt_per_unit,
                args.financing_per_unit,
            )
        )
        landed_contribution_per_unit = (
            expected_net_price - landed_unit_cost - other_variable_cost
        )
        full_sell_through_contribution_potential = (
            landed_contribution_per_unit * args.usable_units
        )

    period_turns = None
    annualized_turns = None
    dio = None
    gmroi = None
    if args.period_cogs is not None:
        period_turns = safe_ratio(args.period_cogs, args.average_inventory_cost)
        if period_turns is not None:
            annualized_turns = period_turns * 365 / args.period_days
        dio_ratio = safe_ratio(args.average_inventory_cost, args.period_cogs)
        if dio_ratio is not None:
            dio = dio_ratio * args.period_days
    if args.gross_margin_dollars is not None:
        gmroi = safe_ratio(args.gross_margin_dollars, args.average_inventory_cost)

    sell_through = None
    if args.units_sold is not None:
        sell_through = safe_ratio(
            args.units_sold, args.beginning_units + args.received_units
        )

    dso = None
    if args.average_receivables is not None:
        dso_ratio = safe_ratio(args.average_receivables, args.net_credit_sales)
        if dso_ratio is not None:
            dso = dso_ratio * args.period_days
    dpo = None
    if args.average_payables is not None:
        dpo_ratio = safe_ratio(args.average_payables, args.credit_purchases)
        if dpo_ratio is not None:
            dpo = dpo_ratio * args.period_days
    cash_conversion_cycle = None
    if dio is not None and dso is not None and dpo is not None:
        cash_conversion_cycle = dio + dso - dpo

    payload_utilization = None
    if args.cargo_weight is not None:
        payload_utilization = args.cargo_weight / args.usable_payload
    cube_utilization = None
    if args.cargo_volume is not None:
        cube_utilization = args.cargo_volume / args.usable_cube
    closer_dimension = None
    if payload_utilization is not None and cube_utilization is not None:
        closer_dimension = (
            "payload" if payload_utilization >= cube_utilization else "cube"
        )

    forecast: list[dict[str, float | int | bool]] = []
    first_floor_breach_week = None
    if args.opening_cash is not None:
        opening = args.opening_cash
        for week, (receipts, outflows) in enumerate(
            zip(args.weekly_receipts, args.weekly_outflows, strict=True), start=1
        ):
            ending = opening + receipts - outflows
            breached = ending < args.cash_floor
            if breached and first_floor_breach_week is None:
                first_floor_breach_week = week
            forecast.append(
                {
                    "week": week,
                    "opening_cash": opening,
                    "receipts": receipts,
                    "outflows": outflows,
                    "ending_cash": ending,
                    "below_cash_floor": breached,
                }
            )
            opening = ending

    flags: list[str] = []
    if landed_contribution_per_unit is not None and landed_contribution_per_unit <= 0:
        flags.append("Landed contribution per unit is not positive.")
    if sell_through is not None and sell_through > 1:
        flags.append(
            "Sell-through exceeds 100%; reconcile the period, units, transfers, and denominator."
        )
    if payload_utilization is not None and payload_utilization > 1:
        flags.append("Cargo weight exceeds the supplied usable payload.")
    if cube_utilization is not None and cube_utilization > 1:
        flags.append("Cargo volume exceeds the supplied usable cube.")
    if (
        payload_utilization is not None
        and cube_utilization is not None
        and payload_utilization > cube_utilization
    ):
        flags.append(
            "Payload is the closer supplied constraint; empty cube alone does not prove usable capacity."
        )
    if first_floor_breach_week is not None:
        flags.append(f"The cash forecast falls below the floor in week {first_floor_breach_week}.")

    return {
        "landed_economics": {
            "total_landed_cost": total_landed_cost,
            "landed_unit_cost": landed_unit_cost,
            "expected_net_price_per_unit": expected_net_price,
            "other_variable_cost_per_unit": other_variable_cost,
            "landed_contribution_per_unit": landed_contribution_per_unit,
            "full_sell_through_contribution_potential": full_sell_through_contribution_potential,
        },
        "inventory_velocity": {
            "period_turns": period_turns,
            "annualized_turns": annualized_turns,
            "days_inventory_outstanding": dio,
            "sell_through": sell_through,
            "gmroi": gmroi,
        },
        "working_capital": {
            "days_sales_outstanding": dso,
            "days_payables_outstanding": dpo,
            "cash_conversion_cycle_days": cash_conversion_cycle,
        },
        "container_utilization": {
            "payload_utilization": payload_utilization,
            "cube_utilization": cube_utilization,
            "closer_supplied_dimension": closer_dimension,
        },
        "cash_forecast": {
            "cash_floor": args.cash_floor if forecast else None,
            "first_floor_breach_week": first_floor_breach_week,
            "weeks": forecast,
        },
        "flags": flags,
        "limitations": [
            "Results depend on consistent units, periods, allocation methods, and reliable source records.",
            "The model does not infer tax, customs, route, axle, handling, damage, compatibility, legal, accounting, or financing rules.",
            "The forecast treats supplied receipts and outflows as scenarios, not verified future cash.",
            "Fixed overhead and tax affect profit even when landed contribution is positive.",
            "Full-sell-through contribution potential assumes every usable unit sells at the modeled unit economics; it is not a cash forecast.",
        ],
    }


def render_text(result: dict[str, Any]) -> str:
    lines: list[str] = []
    for section in (
        "landed_economics",
        "inventory_velocity",
        "working_capital",
        "container_utilization",
    ):
        lines.append(f"{section}:")
        for key, value in result[section].items():
            if value is None:
                rendered = "not computed"
            elif isinstance(value, float):
                rendered = f"{value:.4f}"
            else:
                rendered = str(value)
            lines.append(f"- {key}: {rendered}")
    breach = result["cash_forecast"]["first_floor_breach_week"]
    lines.append(f"first_floor_breach_week: {breach or 'none'}")
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
