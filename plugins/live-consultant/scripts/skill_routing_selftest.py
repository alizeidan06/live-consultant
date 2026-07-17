#!/usr/bin/env python3
"""Regression-test representative Live Consultant multi-skill routes."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_PATH = PLUGIN_ROOT / "assets" / "skill-routing-fixtures.json"
MANIFEST_PATH = PLUGIN_ROOT / "assets" / "skill-knowledge-manifest.json"
SECTION_PATTERN = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)


class DuplicateKeyError(ValueError):
    """Raised when strict JSON loading finds a duplicate object key."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
    )
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return data


def safe_plugin_path(raw: object, label: str, errors: list[str]) -> Path | None:
    if not isinstance(raw, str) or not raw:
        errors.append(f"{label} must be a non-empty string")
        return None
    relative = PurePosixPath(raw)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        errors.append(f"{label} is unsafe: {raw!r}")
        return None
    target = PLUGIN_ROOT.joinpath(*relative.parts)
    try:
        target.resolve().relative_to(PLUGIN_ROOT.resolve())
    except ValueError:
        errors.append(f"{label} escapes the plugin root: {raw!r}")
        return None
    return target


def split_sections(markdown: str) -> dict[str, str]:
    matches = list(SECTION_PATTERN.finditer(markdown))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections[match.group(1)] = markdown[match.end():end]
    return sections


def main() -> int:
    errors: list[str] = []
    traces: list[dict[str, object]] = []
    try:
        fixtures_data = load_json(FIXTURES_PATH)
        manifest = load_json(MANIFEST_PATH)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"errors": [f"fixture load failed: {exc}"]}, indent=2))
        return 1

    if fixtures_data.get("schema_version") != 1:
        errors.append("routing fixtures schema_version must be 1")
    if manifest.get("schema_version") != 1:
        errors.append("skill knowledge manifest schema_version must be 1")

    routing_path = safe_plugin_path(
        fixtures_data.get("routing_map"), "routing_map", errors
    )
    routing_text = ""
    if routing_path is not None:
        if not routing_path.is_file():
            errors.append("routing_map does not exist")
        else:
            routing_text = routing_path.read_text(encoding="utf-8")
    sections = split_sections(routing_text)

    skills = manifest.get("skills")
    if not isinstance(skills, dict):
        errors.append("skill knowledge manifest skills must be an object")
        skills = {}
    fixtures = fixtures_data.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        errors.append("routing fixtures must be a non-empty list")
        fixtures = []

    seen_ids: set[str] = set()
    for index, fixture in enumerate(fixtures):
        label = f"fixtures[{index}]"
        if not isinstance(fixture, dict):
            errors.append(f"{label} must be an object")
            continue
        fixture_id = fixture.get("id")
        section_name = fixture.get("routing_section")
        prompt_summary = fixture.get("prompt_summary")
        required = fixture.get("required_skills")
        if not isinstance(fixture_id, str) or not re.fullmatch(r"[a-z0-9_]+", fixture_id):
            errors.append(f"{label}.id must use lowercase snake_case")
            continue
        if fixture_id in seen_ids:
            errors.append(f"duplicate routing fixture id: {fixture_id}")
        seen_ids.add(fixture_id)
        if not isinstance(prompt_summary, str) or len(prompt_summary.split()) < 8:
            errors.append(f"{fixture_id}: prompt_summary is too thin")
        if not isinstance(section_name, str) or section_name not in sections:
            errors.append(f"{fixture_id}: routing section is missing: {section_name!r}")
            section_text = ""
        else:
            section_text = sections[section_name]
        if (
            not isinstance(required, list)
            or len(required) < 4
            or not all(isinstance(item, str) and item for item in required)
        ):
            errors.append(f"{fixture_id}: required_skills must contain at least four IDs")
            continue
        if len(required) != len(set(required)):
            errors.append(f"{fixture_id}: required_skills contains duplicates")

        markdown_count = 0
        file_count = 0
        for skill_id in required:
            entry = skills.get(skill_id)
            if not isinstance(entry, dict):
                errors.append(f"{fixture_id}: unknown required skill: {skill_id}")
                continue
            if f"`{skill_id}`" not in section_text:
                errors.append(
                    f"{fixture_id}: route section does not explicitly name {skill_id}"
                )
            entrypoint = safe_plugin_path(
                entry.get("entrypoint"), f"{fixture_id}.{skill_id}.entrypoint", errors
            )
            if entrypoint is not None and not entrypoint.is_file():
                errors.append(f"{fixture_id}: missing entrypoint for {skill_id}")
            roots = entry.get("bundle_roots")
            if not isinstance(roots, list) or not roots:
                errors.append(f"{fixture_id}: {skill_id} has no bundle_roots")
                roots = []
            for root_index, raw_root in enumerate(roots):
                root = safe_plugin_path(
                    raw_root,
                    f"{fixture_id}.{skill_id}.bundle_roots[{root_index}]",
                    errors,
                )
                if root is None:
                    continue
                if not root.is_dir():
                    errors.append(f"{fixture_id}: missing bundle root for {skill_id}: {raw_root}")
                    continue
                root_markdown = list(root.rglob("*.md"))
                if not root_markdown:
                    errors.append(f"{fixture_id}: empty Markdown bundle root: {raw_root}")
                markdown_count += len(root_markdown)
            bundle_files = entry.get("bundle_files", [])
            if not isinstance(bundle_files, list):
                errors.append(f"{fixture_id}: {skill_id}.bundle_files must be a list")
                bundle_files = []
            for file_index, raw_file in enumerate(bundle_files):
                bundle_file = safe_plugin_path(
                    raw_file,
                    f"{fixture_id}.{skill_id}.bundle_files[{file_index}]",
                    errors,
                )
                if bundle_file is not None:
                    if not bundle_file.is_file():
                        errors.append(
                            f"{fixture_id}: missing declared bundle file for {skill_id}: {raw_file}"
                        )
                    else:
                        file_count += 1

        traces.append(
            {
                "fixture": fixture_id,
                "required_skills": required,
                "covered_markdown_files": markdown_count,
                "declared_bundle_files": file_count,
            }
        )

    summary = {
        "errors": errors,
        "fixtures": len(fixtures),
        "manifest_skills": len(skills),
        "traces": traces,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
