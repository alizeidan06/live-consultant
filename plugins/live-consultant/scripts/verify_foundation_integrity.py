#!/usr/bin/env python3
"""Verify that Live Consultant's versioned protected foundation is unchanged."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = PLUGIN_ROOT / "assets" / "foundation-lock.json"
MANDATORY_PROTECTED_FILES = {
    "assets/skill-knowledge-manifest.json",
    "assets/skill-routing-fixtures.json",
    "assets/upstream-founder-playbook-manifest.json",
    "assets/templates/sell-like-crazy-system-brief.md",
    "scripts/copy_continuity_selftest.py",
    "scripts/learning_loop.py",
    "scripts/learning_loop_selftest.py",
    "scripts/release_mutation_selftest.py",
    "scripts/skill_routing_selftest.py",
    "scripts/verify_foundation_integrity.py",
    "scripts/verify_knowledge_access.py",
    "scripts/verify_skill_assembly.py",
    "scripts/verify_source_coverage.py",
    "skills/design-offer-funnel/SKILL.md",
    "skills/design-offer-funnel/references/copy-qa.md",
    "skills/design-offer-funnel/references/sales-letter-continuity.md",
    "skills/founder-business-consultant/SKILL.md",
    "skills/founder-business-consultant/references/niche-intelligence-protocol.md",
    "skills/founder-business-consultant/references/knowledge-access-invariant.md",
    "skills/founder-business-consultant/references/routing-map.md",
    "skills/founder-business-consultant/references/skill-assembly-protocol.md",
    "skills/sell-like-crazy/SKILL.md",
    "skills/sell-like-crazy/agents/openai.yaml",
    "skills/sell-like-crazy/references/cases.md",
    "skills/sell-like-crazy/references/examples.md",
    "skills/sell-like-crazy/references/frameworks.md",
    "skills/sell-like-crazy/references/integration.md",
    "skills/sell-like-crazy/references/source-map.md",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("schema_version") != 1:
        raise SystemExit("foundation lock schema_version must be 1")

    protected = lock.get("protected_files")
    if not isinstance(protected, dict) or not protected:
        raise SystemExit("foundation lock has no protected_files")

    errors: list[str] = []
    missing_mandatory = sorted(MANDATORY_PROTECTED_FILES - set(protected))
    for relative in missing_mandatory:
        errors.append(f"mandatory v0.4 foundation file is not locked: {relative}")

    for raw_relative, expected in sorted(protected.items()):
        relative = Path(raw_relative)
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"unsafe protected path: {raw_relative}")
            continue
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            errors.append(f"invalid expected hash: {raw_relative}")
            continue
        target = PLUGIN_ROOT / relative
        if target.is_symlink() or not target.is_file():
            errors.append(f"missing or unsafe protected file: {raw_relative}")
            continue
        actual = sha256(target)
        if actual != expected:
            errors.append(
                f"foundation changed: {raw_relative} expected={expected} actual={actual}"
            )

    if errors:
        print("foundation integrity failed")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "foundation integrity passed: "
        f"{len(protected)} protected files from v{lock.get('baseline_release')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
