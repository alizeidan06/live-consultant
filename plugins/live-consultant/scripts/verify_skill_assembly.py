#!/usr/bin/env python3
"""Verify Live Consultant's complete-skill assembly contract."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PLUGIN_ROOT / "skills"
MANIFEST_PATH = PLUGIN_ROOT / "assets" / "skill-knowledge-manifest.json"
PLUGIN_MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
EXPECTED_BUNDLE_SEMANTICS = "complete_recursive_markdown_plus_declared_files"
SABRI_DEFAULT_PROMPT = (
    "Use $sell-like-crazy to build my complete Dream Buyer-to-sale system."
)
REQUIRED_SKILL_FIELDS = {
    "entrypoint",
    "bundle_roots",
    "contribution",
    "triggers",
    "likely_companions",
}
OPTIONAL_SKILL_FIELDS = {"bundle_files"}
SABRI_SKILL = "sell-like-crazy"
SABRI_REQUIRED_FILES = (
    "agents/openai.yaml",
    "references/frameworks.md",
    "references/cases.md",
    "references/examples.md",
    "references/integration.md",
    "references/source-map.md",
)
SABRI_REQUIRED_TERMS = {
    "SKILL.md": (
        "Load the complete knowledge pack",
        "Governing mindset",
        "Operating sequence",
        "Default output",
        "Sell Like Crazy system brief",
    ),
    "agents/openai.yaml": (
        "Sell Like Crazy System",
        "$sell-like-crazy",
    ),
    "references/frameworks.md": (
        "Foundation: think like a business builder",
        "Phase 1: understand and identify the Dream Buyer",
        "Phase 2: create the perfect bait",
        "Phase 3: capture contact details",
        "Phase 4: build the Godfather Offer",
        "Phase 5: acquire traffic",
        "Phase 6: use the Magic Lantern Technique",
        "Phase 7: convert sales like a doctor",
        "Phase 8: automate and multiply",
        "Larger Market Formula",
        "Power 4%",
        "Halo Strategy",
        "High-Value Content Offer",
        "Godfather Offer",
        "17-step sales-message system",
        "Magic Lantern",
        "The Admission",
        "Fast Action Bonus",
        "Same-call price and payment pressure",
        "embedded-command concept",
        "Artificial pain",
        "Google/PPC click system",
        "Facebook/native attention system",
        "EPC, ROI, and scale volume",
        "Gate 1: get delivered",
        "Gate 2: get opened",
        "Gate 3: get clicked",
        "Five ways to double sales — complete compact field guide",
        "four construction rules",
        "informative, engaging, and relevant",
        "Godfather entry offer and ascension",
    ),
    "references/cases.md": (
        "Merrill Lynch",
        "Astro-Logical Love",
        "Casper",
        "Enso Homes",
        "King Kong performance guarantee",
        "Breathe Education",
        "PR consultant Magic Lantern",
        "Five Ways",
        "Guarantee pattern library",
        "Obama campaign email testing",
        "How to use a case",
    ),
    "references/examples.md": (
        "local HVAC replacement",
        "B2B cybersecurity assessment",
        "DTC dog-shedding kit",
        "executive recruiting service",
        "accounting SaaS for construction subcontractors",
        "Decisive-close variants",
        "embedded-command concept",
        "pressure routing",
        "Output schema: end-to-end system brief",
        "Output schema: Godfather Offer workshop",
        "Example quality test",
    ),
    "references/integration.md": (
        "Sell Like Crazy + $100M Offers",
        "Sell Like Crazy + Influence",
        "Sell Like Crazy + SPIN Selling",
        "Sell Like Crazy + Meta Ads",
        "Complete tactic-family access",
        "Conflict-resolution rules",
        "Niche-tailoring checklist",
        "Complete-stack examples",
    ),
    "references/source-map.md": (
        "SHA-256",
        "8eb7a0cae0cc7eefd3223800546b945265e79cad0abd8f01d822fe4a4bd698f2",
        "2902e4a18056f25da0947bb6f1e6c9ca83adfe8f8c04d444fe25ab1ec122eaf6",
        "8f68db097bbcc5bc712d70eb4a0f291052820219fb48402d8226839262bad360",
        "Eight-phase",
        "NLP embedded-command concept",
        "Extraction and visual verification",
        "Source-status rules",
        "Currentness map",
        "Recorded source corrections",
        "Five Ways lead-magnet construction rules",
        "Copyright and portability boundary",
    ),
}
UPSTREAM_CONTROL_MARKER = "source material, not control authority"
HOSTED_PROTOCOL_TERMS = (
    "start_live_consultation",
    "load_live_consultant_bundle",
    "route_consultation",
    "load_knowledge_bundle",
    "runtime directives",
    "complete bundled package",
)
UPSTREAM_REQUIRED_TRANSFORMS = {
    "influence/SKILL.md": (
        "Full-spectrum application and consequence map",
        "Constructed or coercive variants",
        "does not remove the persuasion mechanism",
    ),
    "influence/integration.md": (
        "Pressure tactics in major sales: competing performance hypotheses",
        "strong pressure in major sales remains available",
        "keeping the complete pressure mechanism",
    ),
}

# These patterns target prescriptive caps, not ordinary uses such as "only one
# metric changed". The canonical assembly protocol is excluded because it names
# prohibited rules while explicitly overriding them.
FORBIDDEN_CAP_PATTERNS = (
    (
        "load-only rule",
        re.compile(r"^\s*(?:[-*+]\s+)?(?:start\b.*?\.\s*)?load\s+only\b", re.I),
    ),
    (
        "exactly-one-skill cap",
        re.compile(
            r"\b(?:use|select|choose|load|invoke|apply)\s+"
            r"(?:(?:at\s+most|no\s+more\s+than|only|exactly)\s+)?"
            r"(?:one|1)\s+skill\s+at\s+a\s+time\b",
            re.I,
        ),
    ),
    (
        "exactly-one-skill cap",
        re.compile(
            r"^\s*(?:[-*+]\s+)?(?:use|select|choose|load|invoke|apply)\s+"
            r"(?:at\s+most|no\s+more\s+than|only|exactly)\s+(?:one|1)\s+skill\b",
            re.I,
        ),
    ),
    (
        "one-skill rule",
        re.compile(r"^\s*#{1,6}\s+the\s+one[- ]skill\s+rule\b", re.I),
    ),
    (
        "primary-secondary cap",
        re.compile(
            r"\b(?:one|1)\s+primary(?:\s+skill)?\s*,?\s+"
            r"(?:one|1)\s+secondary(?:\s+skill)?\s+max\b",
            re.I,
        ),
    ),
    (
        "minimum-specialist restriction",
        re.compile(r"\bminimum\s+specialist\s+skill\b", re.I),
    ),
    (
        "partial-upstream-load rule",
        re.compile(r"\bonly\s+the\s+relevant\s+upstream\s+references\b", re.I),
    ),
)

class DuplicateKeyError(ValueError):
    """Raised when JSON contains a duplicate object key."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_manifest(errors: list[str]) -> dict[str, Any]:
    if not MANIFEST_PATH.is_file():
        errors.append(
            f"missing skill knowledge manifest: {MANIFEST_PATH.relative_to(PLUGIN_ROOT)}"
        )
        return {}
    try:
        loaded = json.loads(
            MANIFEST_PATH.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        errors.append(f"cannot read skill knowledge manifest: {exc}")
        return {}
    if not isinstance(loaded, dict):
        errors.append("skill knowledge manifest must be a JSON object")
        return {}
    return loaded


def resolve_manifest_path(
    raw_path: object,
    label: str,
    errors: list[str],
) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        errors.append(f"{label} must be a non-empty plugin-relative string")
        return None

    path = PurePosixPath(raw_path)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        errors.append(f"{label} is not a safe plugin-relative path: {raw_path!r}")
        return None

    target = PLUGIN_ROOT.joinpath(*path.parts)
    try:
        target.resolve().relative_to(PLUGIN_ROOT.resolve())
    except ValueError:
        errors.append(f"{label} escapes the plugin root: {raw_path!r}")
        return None
    return target


def non_empty_string_list(
    value: object,
    label: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list of strings")
        return []
    if not value and not allow_empty:
        errors.append(f"{label} must not be empty")
        return []
    cleaned: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{label}[{index}] must be a non-empty string")
            continue
        cleaned.append(item)
    if len(cleaned) != len(set(cleaned)):
        errors.append(f"{label} contains duplicate values")
    return cleaned


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def markdown_files(root: Path) -> set[Path]:
    return {
        path
        for path in root.rglob("*.md")
        if path.is_file()
    }


def has_direct_protocol_link(entrypoint: Path, protocol: Path) -> bool:
    try:
        text = entrypoint.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False

    for match in re.finditer(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
        raw_target = match.group(1).strip()
        if raw_target.startswith("<") and raw_target.endswith(">"):
            raw_target = raw_target[1:-1]
        raw_target = raw_target.split("#", 1)[0]
        if not raw_target or "://" in raw_target:
            continue
        candidate = entrypoint.parent / raw_target
        if candidate.resolve() == protocol.resolve():
            return True
    return False


def validate_agent_metadata(skill_name: str, skill_dir: Path, errors: list[str]) -> None:
    path = skill_dir / "agents" / "openai.yaml"
    label = path.relative_to(PLUGIN_ROOT)
    if path.is_symlink() or not path.is_file():
        errors.append(f"missing skill agent metadata: {label}")
        return
    try:
        lines = [
            line.rstrip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read skill agent metadata {label}: {exc}")
        return

    if not lines or lines[0] != "interface:":
        errors.append(f"invalid skill agent metadata root in {label}")
        return

    values: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:], start=2):
        match = re.fullmatch(r'  ([a-z_]+):\s+"([^"\n]+)"', line)
        if match is None:
            errors.append(
                f"invalid skill agent metadata syntax in {label}:{line_number}: {line}"
            )
            continue
        key, value = match.groups()
        if key in values:
            errors.append(f"duplicate skill agent metadata key {key!r} in {label}")
        values[key] = value.strip()

    required = {"display_name", "short_description", "default_prompt"}
    for key in sorted(required - set(values)):
        errors.append(f"skill agent metadata missing {key!r} in {label}")
    for key in sorted(set(values) - required):
        errors.append(f"unknown skill agent metadata key {key!r} in {label}")
    if f"${skill_name}" not in values.get("default_prompt", ""):
        errors.append(
            f"skill agent default_prompt does not invoke ${skill_name} in {label}"
        )


def scan_for_skill_caps(protocol: Path, errors: list[str]) -> None:
    for path in sorted(SKILLS_ROOT.rglob("*.md")):
        if path.resolve() == protocol.resolve() or not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            errors.append(
                f"cannot scan active instruction {path.relative_to(PLUGIN_ROOT)}: {exc}"
            )
            continue
        for line_number, line in enumerate(lines, start=1):
            for label, pattern in FORBIDDEN_CAP_PATTERNS:
                if pattern.search(line):
                    errors.append(
                        f"{label} in active instruction "
                        f"{path.relative_to(PLUGIN_ROOT)}:{line_number}: {line.strip()}"
                    )


def scan_upstream_control_regressions(errors: list[str]) -> None:
    upstream = PLUGIN_ROOT / "assets" / "upstream-founder-playbook"
    for path in sorted(upstream.rglob("*.md")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            errors.append(
                f"cannot scan upstream knowledge {path.relative_to(PLUGIN_ROOT)}: {exc}"
            )
            continue
    for relative, required_phrases in UPSTREAM_REQUIRED_TRANSFORMS.items():
        path = upstream / relative
        if not path.is_file():
            errors.append(f"missing required upstream transform file: {relative}")
            continue
        try:
            content = re.sub(
                r"\s+", " ", path.read_text(encoding="utf-8").lower()
            )
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot verify upstream transform {relative}: {exc}")
            continue
        for phrase in required_phrases:
            if phrase.lower() not in content:
                errors.append(
                    f"upstream transform lost required full-spectrum marker "
                    f"{phrase!r} in {relative}"
                )


def main() -> int:
    errors: list[str] = []
    manifest = load_manifest(errors)

    try:
        plugin_manifest = json.loads(
            PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        errors.append(f"cannot read plugin manifest: {exc}")
        plugin_manifest = {}
    prompts = plugin_manifest.get("interface", {}).get("defaultPrompt", [])
    if not isinstance(prompts, list) or SABRI_DEFAULT_PROMPT not in prompts:
        errors.append(
            "plugin defaultPrompt lost the complete $sell-like-crazy entry point"
        )

    if manifest.get("schema_version") != 1:
        errors.append("skill knowledge manifest schema_version must be 1")
    if manifest.get("bundle_semantics") != EXPECTED_BUNDLE_SEMANTICS:
        errors.append(
            "skill knowledge manifest bundle_semantics must be "
            f"{EXPECTED_BUNDLE_SEMANTICS!r}"
        )

    protocol = resolve_manifest_path(
        manifest.get("assembly_protocol"),
        "assembly_protocol",
        errors,
    )
    if protocol is None:
        protocol = (
            SKILLS_ROOT
            / "founder-business-consultant"
            / "references"
            / "skill-assembly-protocol.md"
        )
    elif protocol.is_symlink() or not protocol.is_file():
        errors.append(
            "assembly_protocol does not resolve to a regular file: "
            f"{protocol.relative_to(PLUGIN_ROOT)}"
        )

    raw_skills = manifest.get("skills")
    if not isinstance(raw_skills, dict):
        errors.append("skill knowledge manifest skills must be an object")
        raw_skills = {}

    actual_skill_dirs = {
        path.name
        for path in SKILLS_ROOT.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    }
    manifested_skills = set(raw_skills)
    for missing in sorted(actual_skill_dirs - manifested_skills):
        errors.append(f"skill directory missing from manifest: {missing}")
    for extra in sorted(manifested_skills - actual_skill_dirs):
        errors.append(f"manifested skill directory does not exist: {extra}")

    covered_markdown: set[Path] = set()
    declared_root_count = 0
    declared_file_count = 0
    entrypoints: dict[str, Path] = {}

    for skill_name in sorted(manifested_skills):
        raw_entry = raw_skills.get(skill_name)
        if not isinstance(raw_entry, dict):
            errors.append(f"skills.{skill_name} must be an object")
            continue

        actual_fields = set(raw_entry)
        for missing_field in sorted(REQUIRED_SKILL_FIELDS - actual_fields):
            errors.append(f"skills.{skill_name} missing field: {missing_field}")
        allowed_fields = REQUIRED_SKILL_FIELDS | OPTIONAL_SKILL_FIELDS
        for unknown_field in sorted(actual_fields - allowed_fields):
            errors.append(f"skills.{skill_name} has unknown field: {unknown_field}")

        contribution = raw_entry.get("contribution")
        if not isinstance(contribution, str) or not contribution.strip():
            errors.append(f"skills.{skill_name}.contribution must be a non-empty string")
        non_empty_string_list(
            raw_entry.get("triggers"),
            f"skills.{skill_name}.triggers",
            errors,
        )
        companions = non_empty_string_list(
            raw_entry.get("likely_companions"),
            f"skills.{skill_name}.likely_companions",
            errors,
            allow_empty=True,
        )
        for companion in companions:
            if companion == skill_name:
                errors.append(f"skills.{skill_name} lists itself as a likely companion")
            elif companion not in manifested_skills:
                errors.append(
                    f"skills.{skill_name} has unknown likely companion: {companion}"
                )

        expected_entrypoint = f"skills/{skill_name}/SKILL.md"
        raw_entrypoint = raw_entry.get("entrypoint")
        if raw_entrypoint != expected_entrypoint:
            errors.append(
                f"skills.{skill_name}.entrypoint must be {expected_entrypoint!r}"
            )
        entrypoint = resolve_manifest_path(
            raw_entrypoint,
            f"skills.{skill_name}.entrypoint",
            errors,
        )
        if entrypoint is not None:
            entrypoints[skill_name] = entrypoint
            if entrypoint.is_symlink() or not entrypoint.is_file():
                errors.append(
                    f"skills.{skill_name}.entrypoint is missing or unsafe: "
                    f"{entrypoint.relative_to(PLUGIN_ROOT)}"
                )

        raw_roots = non_empty_string_list(
            raw_entry.get("bundle_roots"),
            f"skills.{skill_name}.bundle_roots",
            errors,
        )
        raw_files = non_empty_string_list(
            raw_entry.get("bundle_files", []),
            f"skills.{skill_name}.bundle_files",
            errors,
            allow_empty=True,
        )
        required_local_root = f"skills/{skill_name}"
        if required_local_root not in raw_roots:
            errors.append(
                f"skills.{skill_name}.bundle_roots must include {required_local_root!r}"
            )

        resolved_roots: list[Path] = []
        for index, raw_root in enumerate(raw_roots):
            root = resolve_manifest_path(
                raw_root,
                f"skills.{skill_name}.bundle_roots[{index}]",
                errors,
            )
            if root is None:
                continue
            declared_root_count += 1
            if root.is_symlink() or not root.is_dir():
                errors.append(
                    f"skills.{skill_name}.bundle_roots[{index}] is missing or unsafe: "
                    f"{root.relative_to(PLUGIN_ROOT)}"
                )
                continue
            root_markdown = markdown_files(root)
            if not root_markdown:
                errors.append(
                    f"skills.{skill_name}.bundle_roots[{index}] has no Markdown: "
                    f"{root.relative_to(PLUGIN_ROOT)}"
                )
            for markdown in sorted(root_markdown):
                if markdown.is_symlink():
                    errors.append(
                        f"symlinked Markdown is not a safe complete-bundle member: "
                        f"{markdown.relative_to(PLUGIN_ROOT)}"
                    )
            covered_markdown.update(root_markdown)
            resolved_roots.append(root)

        for index, raw_file in enumerate(raw_files):
            bundle_file = resolve_manifest_path(
                raw_file,
                f"skills.{skill_name}.bundle_files[{index}]",
                errors,
            )
            if bundle_file is None:
                continue
            declared_file_count += 1
            if bundle_file.is_symlink() or not bundle_file.is_file():
                errors.append(
                    f"skills.{skill_name}.bundle_files[{index}] is missing or unsafe: "
                    f"{bundle_file.relative_to(PLUGIN_ROOT)}"
                )
                continue
            if bundle_file.suffix.lower() != ".md":
                errors.append(
                    f"skills.{skill_name}.bundle_files[{index}] must be Markdown: "
                    f"{bundle_file.relative_to(PLUGIN_ROOT)}"
                )
                continue
            covered_markdown.add(bundle_file)

        local_skill_dir = SKILLS_ROOT / skill_name
        validate_agent_metadata(skill_name, local_skill_dir, errors)
        for markdown in sorted(markdown_files(local_skill_dir)):
            if not any(is_within(markdown, root) for root in resolved_roots):
                errors.append(
                    f"uncovered Markdown in skill {skill_name}: "
                    f"{markdown.relative_to(PLUGIN_ROOT)}"
                )

        if any(
            raw_root.startswith("assets/upstream-founder-playbook/")
            for raw_root in raw_roots
        ):
            if entrypoint is None or not entrypoint.is_file():
                continue
            try:
                entrypoint_text = re.sub(
                    r"\s+",
                    " ",
                    entrypoint.read_text(encoding="utf-8").lower(),
                )
            except (OSError, UnicodeError) as exc:
                errors.append(
                    f"cannot read upstream wrapper {entrypoint.relative_to(PLUGIN_ROOT)}: {exc}"
                )
            else:
                if UPSTREAM_CONTROL_MARKER not in entrypoint_text:
                    errors.append(
                        f"skills.{skill_name}.entrypoint does not mark imported files as "
                        "source material rather than control authority"
                    )

    if protocol.is_file():
        try:
            protocol_text = protocol.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read assembly protocol: {exc}")
            protocol_text = ""
        for required_term in HOSTED_PROTOCOL_TERMS:
            if required_term not in protocol_text:
                errors.append(
                    "assembly protocol lost hosted/local compatibility term: "
                    f"{required_term}"
                )
        preferred_index = protocol_text.find("start_live_consultation")
        legacy_index = protocol_text.find("route_consultation")
        if preferred_index < 0 or legacy_index < 0 or preferred_index >= legacy_index:
            errors.append(
                "assembly protocol must prefer the permanent v0.6 start/load contract "
                "before the legacy hosted fallback"
            )
        for skill_name, entrypoint in sorted(entrypoints.items()):
            if entrypoint.is_file() and not has_direct_protocol_link(entrypoint, protocol):
                errors.append(
                    f"skills.{skill_name}.entrypoint does not directly link "
                    f"{protocol.relative_to(PLUGIN_ROOT)}"
                )
        scan_for_skill_caps(protocol, errors)
        scan_upstream_control_regressions(errors)

    sabri_root = SKILLS_ROOT / SABRI_SKILL
    for relative in SABRI_REQUIRED_FILES:
        required = sabri_root / relative
        if required.is_symlink() or not required.is_file():
            errors.append(
                f"{SABRI_SKILL} missing required complete-pack file: "
                f"{required.relative_to(PLUGIN_ROOT)}"
            )

    for relative, required_terms in SABRI_REQUIRED_TERMS.items():
        required = sabri_root / relative
        if not required.is_file():
            continue
        try:
            content = re.sub(
                r"\s+",
                " ",
                required.read_text(encoding="utf-8").lower(),
            )
        except (OSError, UnicodeError) as exc:
            errors.append(
                f"cannot read {SABRI_SKILL} semantic pack file "
                f"{required.relative_to(PLUGIN_ROOT)}: {exc}"
            )
            continue
        for term in required_terms:
            if term.lower() not in content:
                errors.append(
                    f"{SABRI_SKILL} semantic pack lost required concept "
                    f"{term!r} in {required.relative_to(PLUGIN_ROOT)}"
                )

    sabri_template = PLUGIN_ROOT / "assets" / "templates" / "sell-like-crazy-system-brief.md"
    sabri_entrypoint = sabri_root / "SKILL.md"
    if sabri_template.is_symlink() or not sabri_template.is_file():
        errors.append("sell-like-crazy reusable system brief template is missing")
    if sabri_entrypoint.is_file() and sabri_template.is_file():
        try:
            if not has_direct_protocol_link(sabri_entrypoint, sabri_template):
                errors.append(
                    "sell-like-crazy entrypoint does not directly link its reusable system brief"
                )
        except OSError as exc:
            errors.append(f"cannot verify sell-like-crazy template link: {exc}")

    sabri_manifest = raw_skills.get(SABRI_SKILL, {})
    if isinstance(sabri_manifest, dict):
        expected_template = "assets/templates/sell-like-crazy-system-brief.md"
        if expected_template not in sabri_manifest.get("bundle_files", []):
            errors.append(
                "sell-like-crazy manifest bundle_files does not include its system brief template"
            )

    result = {
        "manifest": str(MANIFEST_PATH.relative_to(PLUGIN_ROOT)),
        "bundle_semantics": manifest.get("bundle_semantics"),
        "skill_directories": len(actual_skill_dirs),
        "manifested_skills": len(manifested_skills),
        "declared_bundle_roots": declared_root_count,
        "declared_bundle_files": declared_file_count,
        "covered_markdown_files": len(covered_markdown),
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
