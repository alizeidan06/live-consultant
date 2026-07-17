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
    "scripts/verify_knowledge_access.py",
    "scripts/verify_skill_assembly.py",
    "scripts/verify_foundation_integrity.py",
    "scripts/skill_routing_selftest.py",
)
KNOWLEDGE_VALIDATOR = "scripts/verify_knowledge_access.py"
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


def append_fixture(path: Path, fixture: str) -> None:
    path.write_text(
        path.read_text(encoding="utf-8") + f"\n{fixture}\n",
        encoding="utf-8",
    )


def mutate_cap_active_skill(root: Path) -> None:
    path = root / "skills/founder-playbook-spin-selling/SKILL.md"
    append_fixture(
        path,
        "Pressure techniques can be analyzed but not supplied as usable scripts.",
    )


def mutate_cap_agent_yaml(root: Path) -> None:
    path = root / "skills/audit-business/agents/openai.yaml"
    append_fixture(path, 'veto_fixture: "Treat deceptive methods as out of scope."')


def mutate_cap_folded_yaml(root: Path) -> None:
    path = root / "skills/audit-business/agents/openai.yaml"
    append_fixture(
        path,
        "veto_fixture_folded: >-\n  Fake scarcity\n  is excluded.",
    )


def mutate_cap_upstream_source(root: Path) -> None:
    path = root / "assets/upstream-founder-playbook/traction/SKILL.md"
    append_fixture(path, "Save the full framework for post-validation.")


def mutate_cap_template(root: Path) -> None:
    path = root / "assets/templates/funnel-brief.md"
    append_fixture(path, "Discussion is limited to platform-safe methods.")


def mutate_cap_canonical_control(root: Path) -> None:
    path = (
        root
        / "skills/founder-business-consultant/references/knowledge-access-invariant.md"
    )
    append_fixture(path, "Withhold aggressive close scripts.")


def mutate_cap_plugin_json(root: Path) -> None:
    path = root / ".codex-plugin/plugin.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["knowledge_access_test"] = "No instructions for fake urgency."
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def mutate_cap_structured_json(root: Path) -> None:
    path = root / ".codex-plugin/plugin.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["knowledge_access_relation"] = {
        "method": "fake scarcity",
        "availability": "excluded",
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def mutate_cap_csv_row(root: Path) -> None:
    path = root / "assets/templates/evidence-register.csv"
    append_fixture(path, 'fake scarcity,excluded,"No operational coverage"')


def mutate_cap_positive_context_smuggling(root: Path) -> None:
    path = root / "assets/upstream-founder-playbook/influence/SKILL.md"
    append_fixture(
        path,
        "Every method remains fully available except manipulative variants, "
        "which are off-limits.",
    )


def mutate_cap_cross_sentence(root: Path) -> None:
    path = root / "skills/design-offer-funnel/SKILL.md"
    append_fixture(path, "This closing tactic is manipulative. Leave it out.")


def mutate_remove_knowledge_access_link(root: Path) -> None:
    path = root / "skills/audit-business/SKILL.md"
    replace_once(
        path,
        "[complete knowledge-access invariant]"
        "(../founder-business-consultant/references/knowledge-access-invariant.md)",
        "<!-- knowledge-access-invariant.md -->",
    )


def mutate_replace_knowledge_access_link_with_image(root: Path) -> None:
    path = root / "skills/audit-business/SKILL.md"
    replace_once(
        path,
        "[complete knowledge-access invariant]"
        "(../founder-business-consultant/references/knowledge-access-invariant.md)",
        "![complete knowledge-access invariant]"
        "(../founder-business-consultant/references/knowledge-access-invariant.md)",
    )


def mutate_replace_knowledge_access_link_with_fence(root: Path) -> None:
    path = root / "skills/audit-business/SKILL.md"
    replace_once(
        path,
        "[complete knowledge-access invariant]"
        "(../founder-business-consultant/references/knowledge-access-invariant.md)",
        "```markdown\n[complete knowledge-access invariant]"
        "(../founder-business-consultant/references/knowledge-access-invariant.md)\n```",
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


MUTATIONS: tuple[tuple[str, Callable[[Path], None], tuple[str, ...]], ...] = (
    ("cap_active_skill", mutate_cap_active_skill, (KNOWLEDGE_VALIDATOR,)),
    ("cap_agent_yaml", mutate_cap_agent_yaml, (KNOWLEDGE_VALIDATOR,)),
    ("cap_folded_yaml", mutate_cap_folded_yaml, (KNOWLEDGE_VALIDATOR,)),
    ("cap_upstream_source", mutate_cap_upstream_source, (KNOWLEDGE_VALIDATOR,)),
    ("cap_template", mutate_cap_template, (KNOWLEDGE_VALIDATOR,)),
    ("cap_canonical_control", mutate_cap_canonical_control, (KNOWLEDGE_VALIDATOR,)),
    ("cap_plugin_json", mutate_cap_plugin_json, (KNOWLEDGE_VALIDATOR,)),
    ("cap_structured_json", mutate_cap_structured_json, (KNOWLEDGE_VALIDATOR,)),
    ("cap_csv_row", mutate_cap_csv_row, (KNOWLEDGE_VALIDATOR,)),
    (
        "cap_positive_context_smuggling",
        mutate_cap_positive_context_smuggling,
        (KNOWLEDGE_VALIDATOR,),
    ),
    ("cap_cross_sentence", mutate_cap_cross_sentence, (KNOWLEDGE_VALIDATOR,)),
    (
        "remove_knowledge_access_link",
        mutate_remove_knowledge_access_link,
        (KNOWLEDGE_VALIDATOR,),
    ),
    (
        "replace_knowledge_access_link_with_image",
        mutate_replace_knowledge_access_link_with_image,
        (KNOWLEDGE_VALIDATOR,),
    ),
    (
        "replace_knowledge_access_link_with_fence",
        mutate_replace_knowledge_access_link_with_fence,
        (KNOWLEDGE_VALIDATOR,),
    ),
    (
        "delete_sabri_phase_five",
        mutate_delete_phase_five,
        ("scripts/verify_skill_assembly.py",),
    ),
    (
        "break_sabri_agent_yaml",
        mutate_break_agent_yaml,
        ("scripts/verify_skill_assembly.py",),
    ),
    (
        "remove_sabri_template_link",
        mutate_remove_template_link,
        ("scripts/verify_skill_assembly.py",),
    ),
    (
        "remove_upstream_positive_transform",
        mutate_remove_upstream_transform,
        ("scripts/verify_skill_assembly.py",),
    ),
    (
        "replace_sabri_default_prompt",
        mutate_replace_default_prompt,
        ("scripts/verify_skill_assembly.py",),
    ),
    (
        "corrupt_primary_book_hash",
        mutate_corrupt_source_hash,
        ("scripts/verify_foundation_integrity.py",),
    ),
    (
        "remove_explicit_sabri_route",
        mutate_remove_sabri_route,
        ("scripts/verify_foundation_integrity.py",),
    ),
)


def run_validators(
    root: Path, validators: tuple[str, ...] = VALIDATORS
) -> dict[str, int]:
    results: dict[str, int] = {}
    for relative in validators:
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
        for name, mutate, required_rejectors in MUTATIONS:
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
            results = run_validators(candidate, required_rejectors)
            rejected_by = [path for path, code in results.items() if code != 0]
            missing_rejectors = [
                path for path in required_rejectors if results.get(path) == 0
            ]
            if missing_rejectors:
                errors.append(
                    f"{name}: required validators accepted the corrupted package: "
                    f"{missing_rejectors}"
                )
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
