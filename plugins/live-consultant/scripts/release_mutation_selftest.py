#!/usr/bin/env python3
"""Prove that critical Live Consultant release regressions are rejected."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = (
    "scripts/verify_skill_assembly.py",
    "scripts/verify_foundation_integrity.py",
    "scripts/skill_routing_selftest.py",
)
BOOK_SHA256 = "8eb7a0cae0cc7eefd3223800546b945265e79cad0abd8f01d822fe4a4bd698f2"
SABRI_DEFAULT_PROMPT = (
    "Use $sell-like-crazy to build my complete Dream Buyer-to-sale system."
)


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(
            f"mutation precondition failed for {path.name}: expected one {old!r}"
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def mutate_restore_pressure_veto(root: Path) -> None:
    path = root / "skills/founder-playbook-spin-selling/SKILL.md"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\nReject psychological pressure, artificial pain, forced admissions, "
        "and high-pressure closing.\n",
        encoding="utf-8",
    )


def mutate_restore_exact_user_wording_veto(root: Path) -> None:
    path = root / "skills/founder-playbook-spin-selling/SKILL.md"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\nIf it is psychological pressure or faking a problem, then do not "
        "share it and that overrides everything.\n",
        encoding="utf-8",
    )


def mutate_delete_phase_five(root: Path) -> None:
    path = root / "skills/sell-like-crazy/references/frameworks.md"
    text = path.read_text(encoding="utf-8")
    rendered, count = re.subn(
        r"## Phase 5: acquire traffic.*?(?=## Phase 6:)",
        "## Phase 5: acquire traffic\n\n",
        text,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise RuntimeError("could not isolate Phase 5 for mutation")
    path.write_text(rendered, encoding="utf-8")


def mutate_break_agent_yaml(root: Path) -> None:
    path = root / "skills/sell-like-crazy/agents/openai.yaml"
    path.write_text("interface:\n  display_name: [\n", encoding="utf-8")


def mutate_remove_template_link(root: Path) -> None:
    path = root / "skills/sell-like-crazy/SKILL.md"
    replace_once(
        path,
        "../../assets/templates/sell-like-crazy-system-brief.md",
        "missing-system-brief.md",
    )


def mutate_remove_upstream_transform(root: Path) -> None:
    path = root / "assets/upstream-founder-playbook/influence/SKILL.md"
    replace_once(
        path,
        "Full-spectrum application and consequence map",
        "Application notes",
    )


def mutate_replace_default_prompt(root: Path) -> None:
    path = root / ".codex-plugin/plugin.json"
    replace_once(path, SABRI_DEFAULT_PROMPT, "Give me generic marketing advice.")


def mutate_corrupt_source_hash(root: Path) -> None:
    path = root / "skills/sell-like-crazy/references/source-map.md"
    replace_once(path, BOOK_SHA256, "0" * 64)


def mutate_remove_sabri_route(root: Path) -> None:
    path = root / "skills/founder-business-consultant/references/routing-map.md"
    text = path.read_text(encoding="utf-8")
    rendered, count = re.subn(
        r"^\| Sabri Suby, Sell Like Crazy, King Kong, Halo, Godfather, Magic Lantern, or a complete buyer-to-sale system \|.*\n",
        "",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise RuntimeError("could not find explicit Sabri routing row")
    path.write_text(rendered, encoding="utf-8")


MUTATIONS: tuple[tuple[str, Callable[[Path], None]], ...] = (
    ("restore_blanket_pressure_veto", mutate_restore_pressure_veto),
    ("restore_exact_user_wording_veto", mutate_restore_exact_user_wording_veto),
    ("delete_sabri_phase_five", mutate_delete_phase_five),
    ("break_sabri_agent_yaml", mutate_break_agent_yaml),
    ("remove_sabri_template_link", mutate_remove_template_link),
    ("remove_upstream_positive_transform", mutate_remove_upstream_transform),
    ("replace_sabri_default_prompt", mutate_replace_default_prompt),
    ("corrupt_primary_book_hash", mutate_corrupt_source_hash),
    ("remove_explicit_sabri_route", mutate_remove_sabri_route),
)


def run_validators(root: Path) -> dict[str, int]:
    results: dict[str, int] = {}
    for relative in VALIDATORS:
        completed = subprocess.run(
            [sys.executable, str(root / relative)],
            cwd=root,
            text=True,
            capture_output=True,
        )
        results[relative] = completed.returncode
    return results


def main() -> int:
    errors: list[str] = []
    traces: list[dict[str, object]] = []
    baseline = run_validators(PLUGIN_ROOT)
    if any(code != 0 for code in baseline.values()):
        errors.append(f"baseline validators must pass before mutation: {baseline}")

    with tempfile.TemporaryDirectory(prefix="live-consultant-mutations-") as temporary:
        temporary_root = Path(temporary)
        for name, mutate in MUTATIONS:
            candidate = temporary_root / name / "live-consultant"
            shutil.copytree(
                PLUGIN_ROOT,
                candidate,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
            )
            try:
                mutate(candidate)
            except (OSError, RuntimeError, UnicodeError) as exc:
                errors.append(f"{name}: mutation failed: {exc}")
                continue
            results = run_validators(candidate)
            rejected_by = [path for path, code in results.items() if code != 0]
            if not rejected_by:
                errors.append(f"{name}: every validator accepted the corrupted package")
            traces.append(
                {
                    "mutation": name,
                    "rejected": bool(rejected_by),
                    "rejected_by": rejected_by,
                }
            )

    summary = {
        "baseline": baseline,
        "errors": errors,
        "mutations": len(MUTATIONS),
        "traces": traces,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
