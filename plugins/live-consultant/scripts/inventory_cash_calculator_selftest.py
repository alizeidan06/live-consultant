#!/usr/bin/env python3
"""Regression tests for the deterministic inventory and cash calculator."""

from __future__ import annotations

import argparse
import importlib.util
import math
from pathlib import Path


SCRIPT = Path(__file__).with_name("inventory_cash_calculator.py")
SPEC = importlib.util.spec_from_file_location("inventory_cash_calculator", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise SystemExit("cannot load inventory_cash_calculator.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

LANDED_FIELDS = (
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


def approx(actual: float | None, expected: float, label: str) -> None:
    if actual is None or not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9):
        raise AssertionError(f"{label}: expected {expected}, got {actual}")


def clear_fields(namespace: argparse.Namespace, fields: tuple[str, ...]) -> None:
    for field in fields:
        setattr(namespace, field, None)


def baseline() -> argparse.Namespace:
    return argparse.Namespace(
        supplier_cost=50_000.0,
        origin_handling=0.0,
        freight_insurance=6_000.0,
        duties_tariffs=2_000.0,
        customs_brokerage=1_000.0,
        inland_transport=1_000.0,
        inspection_handling=0.0,
        other_shipment_cost=0.0,
        usable_units=5_000.0,
        selling_price=21.0,
        discount_per_unit=0.0,
        return_rate=0.0,
        commission_per_unit=1.0,
        delivery_per_unit=1.0,
        fees_per_unit=0.5,
        warranty_bad_debt_per_unit=0.5,
        financing_per_unit=0.0,
        period_days=90.0,
        period_cogs=180_000.0,
        average_inventory_cost=150_000.0,
        gross_margin_dollars=72_000.0,
        units_sold=800.0,
        beginning_units=900.0,
        received_units=100.0,
        average_receivables=64_000.0,
        net_credit_sales=180_000.0,
        average_payables=56_000.0,
        credit_purchases=180_000.0,
        cargo_weight=26_000.0,
        usable_payload=27_000.0,
        cargo_volume=40.0,
        usable_cube=67.0,
        opening_cash=48_000.0,
        weekly_receipts=[22_000.0] * 13,
        weekly_outflows=[25_000.0] * 13,
        cash_floor=25_000.0,
        format="json",
    )


def main() -> int:
    result = MODULE.compute(baseline())
    approx(result["landed_economics"]["landed_unit_cost"], 12.0, "landed cost")
    approx(
        result["landed_economics"]["landed_contribution_per_unit"],
        6.0,
        "unit contribution",
    )
    approx(result["inventory_velocity"]["period_turns"], 1.2, "turns")
    approx(result["inventory_velocity"]["days_inventory_outstanding"], 75.0, "DIO")
    approx(result["inventory_velocity"]["sell_through"], 0.8, "sell-through")
    approx(result["inventory_velocity"]["gmroi"], 0.48, "GMROI")
    approx(result["working_capital"]["days_sales_outstanding"], 32.0, "DSO")
    approx(result["working_capital"]["days_payables_outstanding"], 28.0, "DPO")
    approx(result["working_capital"]["cash_conversion_cycle_days"], 79.0, "CCC")
    approx(
        result["container_utilization"]["payload_utilization"],
        26_000 / 27_000,
        "payload utilization",
    )
    approx(
        result["container_utilization"]["cube_utilization"],
        40 / 67,
        "cube utilization",
    )
    assert result["container_utilization"]["closer_supplied_dimension"] == "payload"
    assert result["cash_forecast"]["first_floor_breach_week"] == 8
    assert any("empty cube" in flag.lower() for flag in result["flags"])

    zero = baseline()
    zero.period_cogs = 0.0
    zero.average_inventory_cost = 0.0
    zero.gross_margin_dollars = 0.0
    result = MODULE.compute(zero)
    assert result["inventory_velocity"]["period_turns"] is None
    assert result["inventory_velocity"]["days_inventory_outstanding"] is None
    assert result["inventory_velocity"]["gmroi"] is None

    incomplete = baseline()
    incomplete.period_days = None
    try:
        MODULE.compute(incomplete)
    except ValueError as exc:
        assert "requires all related inputs" in str(exc)
    else:
        raise AssertionError("incomplete period inputs must fail")

    dso_only = baseline()
    dso_only.period_cogs = None
    dso_only.average_inventory_cost = None
    dso_only.gross_margin_dollars = None
    dso_only.average_payables = None
    dso_only.credit_purchases = None
    result = MODULE.compute(dso_only)
    assert result["inventory_velocity"]["period_turns"] is None
    approx(result["working_capital"]["days_sales_outstanding"], 32.0, "DSO only")
    assert result["working_capital"]["days_payables_outstanding"] is None
    assert result["working_capital"]["cash_conversion_cycle_days"] is None

    turns_only = baseline()
    turns_only.average_receivables = None
    turns_only.net_credit_sales = None
    turns_only.average_payables = None
    turns_only.credit_purchases = None
    result = MODULE.compute(turns_only)
    approx(result["inventory_velocity"]["period_turns"], 1.2, "turns only")
    assert result["working_capital"]["days_sales_outstanding"] is None
    assert result["working_capital"]["days_payables_outstanding"] is None

    gmroi_only = baseline()
    gmroi_only.period_days = None
    gmroi_only.period_cogs = None
    gmroi_only.average_receivables = None
    gmroi_only.net_credit_sales = None
    gmroi_only.average_payables = None
    gmroi_only.credit_purchases = None
    result = MODULE.compute(gmroi_only)
    approx(result["inventory_velocity"]["gmroi"], 0.48, "GMROI only")
    assert result["inventory_velocity"]["period_turns"] is None

    negative_margin = baseline()
    negative_margin.gross_margin_dollars = -15_000.0
    result = MODULE.compute(negative_margin)
    approx(result["inventory_velocity"]["gmroi"], -0.1, "negative GMROI")

    inconsistent_sell_through = baseline()
    inconsistent_sell_through.units_sold = 1_200.0
    result = MODULE.compute(inconsistent_sell_through)
    approx(result["inventory_velocity"]["sell_through"], 1.2, "sell-through over one")
    assert any("exceeds 100%" in flag for flag in result["flags"])

    forecast_only = baseline()
    clear_fields(forecast_only, LANDED_FIELDS)
    clear_fields(
        forecast_only,
        (
            "period_days",
            "period_cogs",
            "average_inventory_cost",
            "gross_margin_dollars",
            "units_sold",
            "beginning_units",
            "received_units",
            "average_receivables",
            "net_credit_sales",
            "average_payables",
            "credit_purchases",
            "cargo_weight",
            "usable_payload",
            "cargo_volume",
            "usable_cube",
        ),
    )
    result = MODULE.compute(forecast_only)
    assert result["landed_economics"]["total_landed_cost"] is None
    assert result["cash_forecast"]["first_floor_breach_week"] == 8

    ccc_only = baseline()
    clear_fields(ccc_only, LANDED_FIELDS)
    clear_fields(
        ccc_only,
        (
            "gross_margin_dollars",
            "units_sold",
            "beginning_units",
            "received_units",
            "cargo_weight",
            "usable_payload",
            "cargo_volume",
            "usable_cube",
            "opening_cash",
            "weekly_receipts",
            "weekly_outflows",
        ),
    )
    result = MODULE.compute(ccc_only)
    approx(result["working_capital"]["cash_conversion_cycle_days"], 79.0, "CCC only")
    assert result["landed_economics"]["landed_unit_cost"] is None

    discount = baseline()
    discount.discount_per_unit = 22.0
    try:
        MODULE.compute(discount)
    except ValueError as exc:
        assert "cannot exceed" in str(exc)
    else:
        raise AssertionError("discount above price must fail")

    empty = baseline()
    clear_fields(empty, LANDED_FIELDS)
    clear_fields(
        empty,
        (
            "period_days",
            "period_cogs",
            "average_inventory_cost",
            "gross_margin_dollars",
            "units_sold",
            "beginning_units",
            "received_units",
            "average_receivables",
            "net_credit_sales",
            "average_payables",
            "credit_purchases",
            "cargo_weight",
            "usable_payload",
            "cargo_volume",
            "usable_cube",
            "opening_cash",
            "weekly_receipts",
            "weekly_outflows",
        ),
    )
    try:
        MODULE.compute(empty)
    except ValueError as exc:
        assert "at least one complete metric group" in str(exc)
    else:
        raise AssertionError("an empty calculation must fail")

    print("inventory cash calculator self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
