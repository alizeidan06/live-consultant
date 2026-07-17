#!/usr/bin/env python3
"""Regression tests for deterministic public-release metadata."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

from release_metadata import (
    extract_changelog_entry,
    load_release_metadata,
    validate_version_transition,
    verify_existing_release,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    changelog = (
        "# Changelog\n\n"
        "## 1.2.3 - 2026-07-17\n\n"
        "- Exact first bullet.\n"
        "- Exact second bullet.\n\n"
        "## 1.2.2 - 2026-07-16\n\n"
        "- Older release.\n"
    )
    expected_notes = (
        "## 1.2.3 - 2026-07-17\n\n"
        "- Exact first bullet.\n"
        "- Exact second bullet.\n"
    )
    require(
        extract_changelog_entry(changelog, "1.2.3") == expected_notes,
        "changelog entry was not extracted exactly",
    )

    transition = validate_version_transition(
        current_manifest=json.dumps({"version": "1.2.3"}),
        current_changelog=changelog,
        base_manifest=json.dumps({"version": "1.2.2"}),
        base_changelog="# Changelog\n\n## 1.2.2 - 2026-07-16\n\n- Older.\n",
        changed_paths=["CHANGELOG.md", "README.md"],
    )
    require(transition["current_version"] == "1.2.3", "valid version bump failed")

    invalid_transitions = (
        (
            "same-version changed tree",
            dict(
                current_manifest=json.dumps({"version": "1.2.2"}),
                current_changelog="# Changelog\n\n## 1.2.2\n\n- Same.\n",
                base_manifest=json.dumps({"version": "1.2.2"}),
                base_changelog="# Changelog\n\n## 1.2.2\n\n- Same.\n",
                changed_paths=["README.md"],
            ),
        ),
        (
            "missing changelog change",
            dict(
                current_manifest=json.dumps({"version": "1.2.3"}),
                current_changelog=changelog,
                base_manifest=json.dumps({"version": "1.2.2"}),
                base_changelog="# Changelog\n\n## 1.2.2\n\n- Older.\n",
                changed_paths=["README.md"],
            ),
        ),
        (
            "reused changelog entry",
            dict(
                current_manifest=json.dumps({"version": "1.2.3"}),
                current_changelog=changelog,
                base_manifest=json.dumps({"version": "1.2.2"}),
                base_changelog=changelog,
                changed_paths=["CHANGELOG.md", ".github/workflows/release.yml"],
            ),
        ),
    )
    for label, arguments in invalid_transitions:
        try:
            validate_version_transition(**arguments)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{label} was accepted")

    for bad_changelog in (
        "# Changelog\n\n## 9.9.9\n\n- Wrong version.\n",
        changelog + "\n## 1.2.3\n\n- Duplicate.\n",
    ):
        try:
            extract_changelog_entry(bad_changelog, "1.2.3")
        except ValueError:
            pass
        else:
            raise AssertionError("missing or duplicate changelog entry was accepted")

    with tempfile.TemporaryDirectory(prefix="live-consultant-release-metadata-") as temporary:
        root = Path(temporary)
        manifest = root / "plugins/live-consultant/.codex-plugin/plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            json.dumps(
                {
                    "name": "live-consultant",
                    "version": "1.2.3",
                    "interface": {"displayName": "Live Consultant"},
                }
            ),
            encoding="utf-8",
        )
        (root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
        metadata = load_release_metadata(root)
        require(metadata.tag == "v1.2.3", "wrong immutable tag")
        require(metadata.title == "Live Consultant v1.2.3", "wrong release title")
        require(metadata.notes == expected_notes, "wrong release notes")

        release = {
            "tagName": metadata.tag,
            "name": metadata.title,
            "body": metadata.notes.rstrip("\n"),
            "isDraft": False,
            "isPrerelease": False,
        }
        require(not verify_existing_release(release, metadata), "matching release was rejected")
        release["body"] = "Changed after publication"
        require(
            verify_existing_release(release, metadata)
            == ["existing release body differs from the exact CHANGELOG entry"],
            "mutated release was not rejected",
        )

    print(
        "release metadata self-test passed: version transition, exact extraction, "
        "and immutable verification"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
