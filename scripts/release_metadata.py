#!/usr/bin/env python3
"""Derive and verify immutable GitHub release metadata from the package."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEMVER = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
SEMVER_PATTERN = re.compile(rf"^{SEMVER}$")
SECTION_PATTERN = re.compile(r"(?m)^##[ \t]+(?P<label>[^\r\n]+?)[ \t]*$")
VERSION_HEADING_PATTERN = re.compile(
    rf"(?m)^##[ \t]+(?P<version>{SEMVER})(?:[ \t]+-[ \t]+\d{{4}}-\d{{2}}-\d{{2}})?[ \t]*$"
)


@dataclass(frozen=True, order=True)
class SemVer:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str, label: str) -> "SemVer":
        match = SEMVER_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError(f"{label} is not release semver: {value!r}")
        return cls(*(int(part) for part in value.split(".")))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True)
class ReleaseMetadata:
    version: str
    tag: str
    title: str
    notes: str


def manifest_version(text: str, label: str) -> SemVer:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is invalid JSON: {exc}") from exc
    value = payload.get("version")
    if not isinstance(value, str):
        raise ValueError(f"{label} has no string version")
    return SemVer.parse(value, f"{label} version")


def changelog_versions(text: str) -> list[SemVer]:
    return [
        SemVer.parse(match.group("version"), "CHANGELOG heading")
        for match in VERSION_HEADING_PATTERN.finditer(text)
    ]


def validate_version_transition(
    *,
    current_manifest: str,
    current_changelog: str,
    base_manifest: str,
    base_changelog: str,
    changed_paths: list[str],
) -> dict[str, object]:
    """Require every changed public tree to become one new immutable release."""

    current = manifest_version(current_manifest, "current plugin manifest")
    base = manifest_version(base_manifest, "base plugin manifest")
    headings = changelog_versions(current_changelog)
    if not headings or headings[0] != current:
        newest = str(headings[0]) if headings else "missing"
        raise ValueError(
            f"newest CHANGELOG entry {newest} does not match plugin {current}"
        )

    summary: dict[str, object] = {
        "base_version": str(base),
        "current_version": str(current),
        "changed_paths": changed_paths,
    }
    if not changed_paths:
        return summary
    if current <= base:
        raise ValueError(
            "public tree changed without a strictly higher release version: "
            f"base={base}, current={current}"
        )
    if "CHANGELOG.md" not in changed_paths:
        raise ValueError("public tree changed without updating CHANGELOG.md")
    if current in changelog_versions(base_changelog):
        raise ValueError(
            f"CHANGELOG entry {current} already existed at the base commit"
        )
    return summary


def extract_changelog_entry(changelog: str, version: str) -> str:
    """Return one version section without rewriting any internal content."""

    if not SEMVER_PATTERN.fullmatch(version):
        raise ValueError(f"plugin version is not release semver: {version!r}")

    headings = list(SECTION_PATTERN.finditer(changelog))
    version_heading = re.compile(
        rf"^{re.escape(version)}(?:[ \t]+-[ \t]+\d{{4}}-\d{{2}}-\d{{2}})?$"
    )
    matches = [heading for heading in headings if version_heading.fullmatch(heading.group("label"))]
    if len(matches) != 1:
        raise ValueError(
            f"CHANGELOG.md must contain exactly one level-two entry for {version}; found {len(matches)}"
        )

    match = matches[0]
    following = next((heading for heading in headings if heading.start() > match.start()), None)
    end = following.start() if following else len(changelog)
    # Boundary-only newline normalization makes GitHub API round trips stable;
    # every character inside the changelog entry remains byte-for-byte exact.
    return changelog[match.start() : end].rstrip("\r\n") + "\n"


def load_release_metadata(root: Path = ROOT) -> ReleaseMetadata:
    manifest_path = root / "plugins/live-consultant/.codex-plugin/plugin.json"
    changelog_path = root / "CHANGELOG.md"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        changelog = changelog_path.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"release metadata read failed: {exc}") from exc

    version = manifest.get("version")
    if not isinstance(version, str) or not SEMVER_PATTERN.fullmatch(version):
        raise ValueError(f"plugin version is not release semver: {version!r}")

    interface = manifest.get("interface")
    display_name = interface.get("displayName") if isinstance(interface, dict) else None
    if not isinstance(display_name, str) or not display_name.strip():
        raise ValueError("plugin displayName is missing")
    if any(character in display_name for character in "\r\n"):
        raise ValueError("plugin displayName must fit on one line")

    return ReleaseMetadata(
        version=version,
        tag=f"v{version}",
        title=f"{display_name.strip()} v{version}",
        notes=extract_changelog_entry(changelog, version),
    )


def normalized_release_body(value: str) -> str:
    return value.rstrip("\r\n") + "\n"


def verify_existing_release(payload: Any, metadata: ReleaseMetadata) -> list[str]:
    if not isinstance(payload, dict):
        return ["GitHub release response is not an object"]

    errors: list[str] = []
    expected = {
        "tagName": metadata.tag,
        "name": metadata.title,
        "isDraft": False,
        "isPrerelease": False,
    }
    for field, expected_value in expected.items():
        if payload.get(field) != expected_value:
            errors.append(
                f"existing release {field} is {payload.get(field)!r}, expected {expected_value!r}"
            )

    body = payload.get("body")
    if not isinstance(body, str) or normalized_release_body(body) != metadata.notes:
        errors.append("existing release body differs from the exact CHANGELOG entry")
    return errors


def write_github_output(path: Path, metadata: ReleaseMetadata) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(f"version={metadata.version}\n")
        stream.write(f"tag={metadata.tag}\n")
        stream.write(f"title={metadata.title}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--notes-file", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--verify-release-json", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        metadata = load_release_metadata(args.root.resolve())
        args.notes_file.write_text(metadata.notes, encoding="utf-8")
        if args.github_output:
            write_github_output(args.github_output, metadata)
        if args.verify_release_json:
            payload = json.loads(args.verify_release_json.read_text(encoding="utf-8"))
            errors = verify_existing_release(payload, metadata)
            if errors:
                raise ValueError("; ".join(errors))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"release metadata error: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {"tag": metadata.tag, "title": metadata.title, "version": metadata.version},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
