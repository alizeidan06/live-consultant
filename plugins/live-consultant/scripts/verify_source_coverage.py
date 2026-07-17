#!/usr/bin/env python3
"""Verify the pinned upstream source manifest and packaged text snapshot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "assets" / "upstream-founder-playbook-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshot = root / "assets" / "upstream-founder-playbook"

    errors: list[str] = []
    derivative_review = manifest.get("derivative_review", {})
    if derivative_review.get("owner_directive") != 31:
        errors.append("source manifest lost owner directive 31 derivative review")
    if derivative_review.get("scope") != "all packaged Markdown in the pinned source snapshot":
        errors.append("source manifest lost complete Markdown review scope")
    rule = derivative_review.get("rule", "")
    for marker in (
        "Categorical knowledge, ideation, routing, and application limits",
        "source positions",
        "available variants",
        "consequence maps",
    ):
        if marker not in rule:
            errors.append(f"source manifest lost derivative rule marker: {marker}")
    packaged = 0
    omitted = 0
    expected_packaged_paths: set[str] = set()
    for item in manifest["files"]:
        target = snapshot / item["path"]
        if item["packaged"]:
            packaged += 1
            expected_packaged_paths.add(item["path"])
            if not target.is_file():
                errors.append(f"missing packaged file: {item['path']}")
                continue
            if target.stat().st_size != item["bytes"]:
                errors.append(f"size mismatch: {item['path']}")
            if sha256(target) != item["sha256"]:
                errors.append(f"hash mismatch: {item['path']}")
        else:
            omitted += 1
            if target.exists():
                errors.append(f"omitted file unexpectedly packaged: {item['path']}")

    actual_packaged_paths = {
        path.relative_to(snapshot).as_posix()
        for path in snapshot.rglob("*")
        if path.is_file()
    }
    for extra in sorted(actual_packaged_paths - expected_packaged_paths):
        errors.append(f"unmanifested packaged file: {extra}")
    for missing in sorted(expected_packaged_paths - actual_packaged_paths):
        if f"missing packaged file: {missing}" not in errors:
            errors.append(f"missing packaged file: {missing}")

    expected = manifest["tracked_file_count"]
    if packaged + omitted != expected:
        errors.append(
            f"manifest count mismatch: {packaged}+{omitted} != {expected}"
        )

    result = {
        "source": manifest["source"],
        "commit": manifest["commit"],
        "derivative_review": derivative_review,
        "tracked_files": expected,
        "packaged_files": packaged,
        "omitted_files": omitted,
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
