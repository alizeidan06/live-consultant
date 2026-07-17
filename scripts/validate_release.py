#!/usr/bin/env python3
"""Validate the public Live Consultant marketplace without external packages."""

from __future__ import annotations

import argparse
import json
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

from release_metadata import load_release_metadata, validate_version_transition


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "live-consultant"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
MARKER = ROOT / ".live-consultant-public-export.json"

REQUIRED_ROOT_FILES = {
    Path(".agents/plugins/marketplace.json"),
    Path(".github/CODEOWNERS"),
    Path(".github/ISSUE_TEMPLATE/config.yml"),
    Path(".github/ISSUE_TEMPLATE/learning.yml"),
    Path(".github/pull_request_template.md"),
    Path(".github/workflows/release.yml"),
    Path(".github/workflows/validate.yml"),
    Path("CHANGELOG.md"),
    Path("CONTRIBUTING.md"),
    Path("LEARNING_POLICY.md"),
    Path("LICENSE"),
    Path("PRIVACY.md"),
    Path("README.md"),
    Path("scripts/release_metadata.py"),
    Path("scripts/release_metadata_selftest.py"),
    Path("SECURITY.md"),
    Path("TERMS.md"),
    Path("plugins/live-consultant/LICENSE"),
    Path("plugins/live-consultant/assets/foundation-lock.json"),
    Path("plugins/live-consultant/assets/skill-knowledge-manifest.json"),
    Path("plugins/live-consultant/assets/skill-routing-fixtures.json"),
    Path("plugins/live-consultant/assets/upstream-founder-playbook-manifest.json"),
    Path("plugins/live-consultant/assets/templates/niche-context.md"),
    Path("plugins/live-consultant/assets/templates/sell-like-crazy-system-brief.md"),
    Path("plugins/live-consultant/scripts/verify_foundation_integrity.py"),
    Path("plugins/live-consultant/scripts/verify_knowledge_access.py"),
    Path("plugins/live-consultant/scripts/verify_skill_assembly.py"),
    Path("plugins/live-consultant/scripts/verify_source_coverage.py"),
    Path("plugins/live-consultant/scripts/learning_loop.py"),
    Path("plugins/live-consultant/scripts/learning_loop_selftest.py"),
    Path("plugins/live-consultant/scripts/release_mutation_selftest.py"),
    Path("plugins/live-consultant/scripts/skill_routing_selftest.py"),
    Path("plugins/live-consultant/skills/improve-live-consultant/SKILL.md"),
    Path("plugins/live-consultant/skills/improve-live-consultant/references/foundation-invariants.md"),
    Path("plugins/live-consultant/skills/improve-live-consultant/references/learning-protocol.md"),
    Path("plugins/live-consultant/skills/founder-business-consultant/references/niche-intelligence-protocol.md"),
    Path("plugins/live-consultant/skills/founder-business-consultant/references/knowledge-access-invariant.md"),
    Path("plugins/live-consultant/skills/founder-business-consultant/references/skill-assembly-protocol.md"),
    Path("plugins/live-consultant/skills/sell-like-crazy/SKILL.md"),
    Path("plugins/live-consultant/skills/sell-like-crazy/agents/openai.yaml"),
    Path("plugins/live-consultant/skills/sell-like-crazy/references/frameworks.md"),
    Path("plugins/live-consultant/skills/sell-like-crazy/references/cases.md"),
    Path("plugins/live-consultant/skills/sell-like-crazy/references/examples.md"),
    Path("plugins/live-consultant/skills/sell-like-crazy/references/integration.md"),
    Path("plugins/live-consultant/skills/sell-like-crazy/references/source-map.md"),
    Path("plugins/live-consultant/THIRD_PARTY_NOTICES.md"),
}

DISALLOWED_SUFFIXES = {
    ".doc",
    ".docx",
    ".gif",
    ".jpeg",
    ".jpg",
    ".key",
    ".mov",
    ".mp3",
    ".mp4",
    ".pdf",
    ".pem",
    ".png",
    ".pyc",
    ".webp",
}

FORBIDDEN_PATTERNS = {
    "macOS user path": re.compile("/" + "Users/", re.IGNORECASE),
    "iCloud private path": re.compile("Mobile" + " Documents", re.IGNORECASE),
    "private source repository": re.compile(
        "alizeidan06/" + "improving-knowledge-base", re.IGNORECASE
    ),
    "GitHub token": re.compile(r"\b(?:gh[opusr]_[A-Za-z0-9_]{20,})\b"),
    "OpenAI key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}\b"),
    "GitLab token": re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b"),
    "npm token": re.compile(r"\bnpm_[A-Za-z0-9]{30,}\b"),
    "Stripe live key": re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{16,}\b"),
    "credentialed database URL": re.compile(
        r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s/:]+:[^\s/@]+@",
        re.IGNORECASE,
    ),
    "JWT": re.compile(
        r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"
    ),
    "private key": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
}

LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
INLINE_QUOTE_PATTERNS = (
    re.compile(r'"([^"\n]+)"'),
    re.compile(r"“([^”\n]+)”"),
)

EXPECTED_ACTION_PINS = {
    "actions/checkout": "34e114876b0b11c390a56381ad16ebd13914f8d5",
    "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
}
ACTION_USE_PATTERN = re.compile(
    r"(?m)^\s*(?:-\s*)?uses:\s*(?P<action>[^@\s]+)@(?P<revision>[^\s#]+)"
)
ZERO_SHA_PATTERN = re.compile(r"^0{40}$")


def record(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def git_output(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True,
        capture_output=True,
    )


def validate_base_transition(
    errors: list[str],
    *,
    base_ref: str | None,
    require_base: bool,
    current_manifest: str,
    current_changelog: str,
) -> dict[str, object] | None:
    raw = (base_ref or "").strip()
    if not raw or ZERO_SHA_PATTERN.fullmatch(raw):
        if require_base:
            errors.append("public CI requires an exact base commit")
        return None
    if raw.startswith("-") or any(character.isspace() for character in raw):
        errors.append(f"invalid base commit: {raw!r}")
        return None

    resolved = git_output("rev-parse", "--verify", "--end-of-options", f"{raw}^{{commit}}")
    if resolved.returncode != 0:
        errors.append(f"cannot resolve public base commit {raw}: {resolved.stderr.strip()}")
        return None
    base = resolved.stdout.strip()

    changed = git_output("diff", "--name-only", "--diff-filter=ACDMRTUXB", base, "HEAD")
    if changed.returncode != 0:
        errors.append(f"cannot compare public tree with {base}: {changed.stderr.strip()}")
        return None
    changed_paths = sorted(path for path in changed.stdout.splitlines() if path)

    base_manifest = git_output(
        "show", f"{base}:plugins/live-consultant/.codex-plugin/plugin.json"
    )
    base_changelog = git_output("show", f"{base}:CHANGELOG.md")
    if base_manifest.returncode != 0 or base_changelog.returncode != 0:
        errors.append("public base commit is missing its manifest or CHANGELOG.md")
        return None
    try:
        return validate_version_transition(
            current_manifest=current_manifest,
            current_changelog=current_changelog,
            base_manifest=base_manifest.stdout,
            base_changelog=base_changelog.stdout,
            changed_paths=changed_paths,
        )
    except ValueError as exc:
        errors.append(f"public version transition failed: {exc}")
        return None


def parse_skill_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing opening frontmatter delimiter")
    try:
        block = text.split("---\n", 2)[1]
    except IndexError as exc:
        raise ValueError("missing closing frontmatter delimiter") from exc
    values: dict[str, str] = {}
    for line in block.splitlines():
        match = re.match(r"^(name|description):\s*(.+?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2).strip('"\'')
    return values


def validate_local_links(errors: list[str]) -> int:
    checked = 0
    for markdown in sorted(PLUGIN.rglob("*.md")):
        text = markdown.read_text(encoding="utf-8")
        for raw_target in LINK_PATTERN.findall(text):
            target = raw_target.strip().strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue
            checked += 1
            resolved = (markdown.parent / path_part).resolve()
            try:
                resolved.relative_to(PLUGIN.resolve())
            except ValueError:
                errors.append(f"link escapes plugin root: {markdown.relative_to(ROOT)} -> {target}")
                continue
            if not resolved.exists():
                errors.append(f"missing local link: {markdown.relative_to(ROOT)} -> {target}")
    return checked


def quote_block_word_count(lines: list[str]) -> int:
    content = " ".join(re.sub(r"^\s*>\s?", "", line) for line in lines)
    return len(re.findall(r"\b[\w'-]+\b", content))


def validate_long_quotes(errors: list[str]) -> tuple[int, int]:
    block_checked = 0
    inline_checked = 0
    snapshot = PLUGIN / "assets" / "upstream-founder-playbook"
    for markdown in sorted(snapshot.rglob("*.md")):
        lines = markdown.read_text(encoding="utf-8").splitlines()
        index = 0
        while index < len(lines):
            if not lines[index].lstrip().startswith(">"):
                index += 1
                continue
            end = index
            while end < len(lines) and lines[end].lstrip().startswith(">"):
                end += 1
            block = lines[index:end]
            first = block[0].lstrip()
            if first.startswith(('> "', '> **"', "> “", "> **“")):
                block_checked += 1
                if quote_block_word_count(block) > 25:
                    errors.append(
                        f"long quoted block not sanitized: {markdown.relative_to(ROOT)}:{index + 1}"
                    )
            index = end
        if markdown.name == "cases.md":
            for line_number, line in enumerate(lines, 1):
                if line.lstrip().startswith(">"):
                    continue
                for pattern in INLINE_QUOTE_PATTERNS:
                    for match in pattern.finditer(line):
                        inline_checked += 1
                        words = len(re.findall(r"\b[\w'-]+\b", match.group(1)))
                        if words > 25:
                            errors.append(
                                "long inline case quotation not sanitized: "
                                f"{markdown.relative_to(ROOT)}:{line_number}"
                            )
    return block_checked, inline_checked


def validate_action_pins(errors: list[str], workflow: Path, text: str) -> None:
    uses = list(ACTION_USE_PATTERN.finditer(text))
    record(errors, bool(uses), f"workflow has no pinned actions: {workflow.relative_to(ROOT)}")
    seen_actions: set[str] = set()
    for match in uses:
        action = match.group("action")
        revision = match.group("revision")
        seen_actions.add(action)
        record(
            errors,
            bool(re.fullmatch(r"[0-9a-f]{40}", revision)),
            f"workflow action is not pinned to a full commit SHA: {action}@{revision}",
        )
        if action in EXPECTED_ACTION_PINS:
            record(
                errors,
                revision == EXPECTED_ACTION_PINS[action],
                f"workflow action pin is unverified: {action}@{revision}",
            )
        else:
            errors.append(f"workflow uses an unreviewed action: {action}")
    for action in sorted(EXPECTED_ACTION_PINS):
        record(
            errors,
            action in seen_actions,
            f"workflow lost required reviewed action: {workflow.relative_to(ROOT)} -> {action}",
        )


def validate_release_automation(errors: list[str]) -> None:
    validate_path = ROOT / ".github/workflows/validate.yml"
    release_path = ROOT / ".github/workflows/release.yml"
    if not validate_path.is_file() or not release_path.is_file():
        return

    validate_text = validate_path.read_text(encoding="utf-8")
    release_text = release_path.read_text(encoding="utf-8")
    validate_action_pins(errors, validate_path, validate_text)
    validate_action_pins(errors, release_path, release_text)

    record(errors, "pull_request_target" not in validate_text, "privileged pull_request_target is forbidden")
    record(errors, "contents: read" in validate_text, "validation workflow must remain read-only")
    for required in (
        "fetch-depth: 0",
        "persist-credentials: false",
        "github.event.pull_request.base.sha",
        "github.event.before",
        "--base-ref",
        "--require-base",
    ):
        record(
            errors,
            required in validate_text,
            f"validation workflow base-version invariant missing: {required}",
        )
    record(
        errors,
        bool(re.search(r"(?m)^  pull_request:\s*$", validate_text)),
        "validation workflow must run for pull requests",
    )
    record(
        errors,
        bool(
            re.search(
                r"(?m)^  push:\s*\n    branches:\s*\n      - main\s*$",
                validate_text,
            )
        ),
        "validation workflow must limit push validation to main",
    )
    record(
        errors,
        not bool(re.search(r"(?m)^\s+tags(?:-ignore)?:", validate_text)),
        "validation workflow must not start a recursive tag-validation loop",
    )

    for required in (
        "workflow_run:",
        "- Validate public plugin",
        "- completed",
        "contents: write",
        "github.event.workflow_run.conclusion == 'success'",
        "github.event.workflow_run.event == 'push'",
        "github.event.workflow_run.head_branch == 'main'",
        "github.event.workflow_run.head_repository.full_name == github.repository",
        "ref: ${{ github.event.workflow_run.head_sha }}",
        "python3 scripts/release_metadata.py",
        "--verify-release-json",
        "git rev-parse HEAD",
        "git ls-remote origin",
        "existing_sha\" != \"$EXPECTED_SHA",
        "gh release create",
        "--verify-tag",
        "--notes-file",
    ):
        record(errors, required in release_text, f"release workflow invariant missing: {required}")
    record(
        errors,
        not bool(re.search(r"(?m)^  (?:push|pull_request|pull_request_target):", release_text)),
        "release workflow may trigger only after validation through workflow_run",
    )
    record(errors, "release edit" not in release_text, "published releases must never be edited")
    record(
        errors,
        not bool(re.search(r"git\s+push[^\n]*(?:--force|-f(?:\s|$))", release_text)),
        "release workflow must never force-push a tag",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", help="exact public base commit for version policy")
    parser.add_argument(
        "--require-base",
        action="store_true",
        help="fail when the base commit is missing or cannot be resolved",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []

    for relative in sorted(REQUIRED_ROOT_FILES):
        record(errors, (ROOT / relative).is_file(), f"missing required file: {relative}")

    try:
        plugin_manifest_text = (
            PLUGIN / ".codex-plugin" / "plugin.json"
        ).read_text(encoding="utf-8")
        plugin_manifest = json.loads(plugin_manifest_text)
        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        marker = json.loads(MARKER.read_text(encoding="utf-8"))
        source_manifest = json.loads(
            (
                PLUGIN
                / "assets"
                / "upstream-founder-playbook-manifest.json"
            ).read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"manifest read failed: {exc}")
        plugin_manifest_text = "{}"
        plugin_manifest = {}
        marketplace = {}
        marker = {}
        source_manifest = {}

    version = plugin_manifest.get("version", "")
    record(errors, plugin_manifest.get("name") == "live-consultant", "wrong plugin name")
    record(errors, bool(re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", version)), "plugin version is not release semver")
    record(errors, plugin_manifest.get("license") == "MIT", "plugin license is not MIT")
    record(errors, plugin_manifest.get("repository") == "https://github.com/alizeidan06/live-consultant", "wrong public repository URL")
    record(errors, marker.get("plugin") == "live-consultant", "export marker has the wrong plugin identity")
    record(
        errors,
        marker.get("repository") == "https://github.com/alizeidan06/live-consultant",
        "export marker has the wrong repository identity",
    )
    record(errors, marker.get("version") == version, "export marker version does not match plugin")
    record(errors, bool(re.fullmatch(r"[0-9a-f]{40}", marker.get("source_commit", ""))), "export marker lacks a source commit")
    changelog_text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    version_transition = validate_base_transition(
        errors,
        base_ref=args.base_ref,
        require_base=args.require_base,
        current_manifest=plugin_manifest_text,
        current_changelog=changelog_text,
    )
    record(
        errors,
        bool(re.search(rf"(?m)^## {re.escape(version)}(?:\s+-|\s*$)", changelog_text)),
        "CHANGELOG.md has no entry for the plugin version",
    )
    try:
        release_metadata = load_release_metadata(ROOT)
        record(
            errors,
            release_metadata.version == version,
            "release metadata version does not match plugin",
        )
        record(
            errors,
            release_metadata.tag == f"v{version}",
            "release metadata tag is not the immutable version tag",
        )
    except ValueError as exc:
        errors.append(f"release metadata validation failed: {exc}")

    interface = plugin_manifest.get("interface", {})
    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
        record(errors, bool(interface.get(field)), f"plugin interface field missing: {field}")
    prompts = interface.get("defaultPrompt", [])
    record(errors, isinstance(prompts, list) and 1 <= len(prompts) <= 3, "defaultPrompt must contain one to three entries")

    public_transform = source_manifest.get("public_release_transform", {})
    derivative_review = source_manifest.get("derivative_review", {})
    record(
        errors,
        derivative_review.get("owner_directive") == 31,
        "source manifest lost semantic knowledge-access review directive",
    )
    record(
        errors,
        derivative_review.get("scope")
        == "all packaged Markdown in the pinned source snapshot",
        "source manifest lost complete Markdown review scope",
    )
    record(
        errors,
        public_transform.get("excluded_paths")
        == ["README.md", "experiments/real-founder-problems.md"],
        "public source exclusions are missing or changed",
    )
    record(
        errors,
        public_transform.get("long_quote_word_limit") == 25,
        "public quote limit is not recorded",
    )
    record(
        errors,
        public_transform.get("quote_passages_omitted", 0) > 0,
        "public quote sanitization did not run",
    )
    record(
        errors,
        not (PLUGIN / "assets/upstream-founder-playbook/README.md").exists(),
        "excluded upstream README is present",
    )
    record(
        errors,
        not (
            PLUGIN
            / "assets/upstream-founder-playbook/experiments/real-founder-problems.md"
        ).exists(),
        "excluded community-post experiment is present",
    )

    plugins = marketplace.get("plugins", [])
    record(errors, marketplace.get("name") == "live-consultant", "wrong marketplace name")
    record(errors, len(plugins) == 1, "marketplace must contain exactly one plugin")
    if len(plugins) == 1:
        entry = plugins[0]
        record(errors, entry.get("name") == "live-consultant", "wrong marketplace plugin name")
        record(errors, entry.get("source") == {"source": "local", "path": "./plugins/live-consultant"}, "wrong marketplace source")
        record(errors, entry.get("policy") == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "wrong marketplace policy")

    files = 0
    for path in sorted(ROOT.rglob("*")):
        if ".git" in path.parts:
            continue
        if path.is_symlink():
            errors.append(f"symlink rejected: {path.relative_to(ROOT)}")
            continue
        if not path.is_file():
            continue
        files += 1
        relative = path.relative_to(ROOT)
        if path.suffix.lower() in DISALLOWED_SUFFIXES:
            errors.append(f"disallowed file type: {relative}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"non-text file rejected: {relative}")
            continue
        if ("[TO" + "DO:") in text:
            errors.append(f"TODO placeholder found: {relative}")
        for label, pattern in FORBIDDEN_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label} found in {relative}")

    skill_count = 0
    for skill_file in sorted((PLUGIN / "skills").glob("*/SKILL.md")):
        skill_count += 1
        try:
            frontmatter = parse_skill_frontmatter(skill_file)
        except ValueError as exc:
            errors.append(f"invalid skill {skill_file.relative_to(ROOT)}: {exc}")
            continue
        record(errors, frontmatter.get("name") == skill_file.parent.name, f"skill name mismatch: {skill_file.relative_to(ROOT)}")
        record(errors, bool(frontmatter.get("description")), f"skill description missing: {skill_file.relative_to(ROOT)}")
        record(
            errors,
            "communication-voice.md" in skill_file.read_text(encoding="utf-8"),
            f"skill lost universal voice and learning entry point: {skill_file.relative_to(ROOT)}",
        )
        record(
            errors,
            "niche-intelligence-protocol.md" in skill_file.read_text(encoding="utf-8"),
            f"skill lost universal niche intelligence: {skill_file.relative_to(ROOT)}",
        )
        record(
            errors,
            "skill-assembly-protocol.md" in skill_file.read_text(encoding="utf-8"),
            f"skill lost universal knowledge assembly: {skill_file.relative_to(ROOT)}",
        )
        record(
            errors,
            "knowledge-access-invariant.md" in skill_file.read_text(encoding="utf-8"),
            f"skill lost universal complete knowledge access: {skill_file.relative_to(ROOT)}",
        )
    record(errors, skill_count == 24, f"expected 24 skills, found {skill_count}")

    voice_path = (
        PLUGIN
        / "skills"
        / "founder-business-consultant"
        / "references"
        / "communication-voice.md"
    )
    voice_text = voice_path.read_text(encoding="utf-8") if voice_path.is_file() else ""
    record(
        errors,
        "improve-live-consultant/references/learning-protocol.md" in voice_text,
        "universal communication voice lost the learning protocol link",
    )

    niche_path = (
        PLUGIN
        / "skills"
        / "founder-business-consultant"
        / "references"
        / "niche-intelligence-protocol.md"
    )
    niche_text = niche_path.read_text(encoding="utf-8") if niche_path.is_file() else ""
    for required_phrase in (
        "Default to zero questions",
        "never ask more than three",
        "R3 - Execution grade",
        "Never silently transfer evidence",
        "Adapt the implementation, not the foundation",
    ):
        record(
            errors,
            required_phrase in niche_text,
            f"niche protocol lost invariant: {required_phrase}",
        )

    privacy_text = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
    record(errors, "off by default" in privacy_text, "privacy policy lost local-learning opt-in")
    record(errors, "does not call GitHub" in privacy_text, "privacy policy lost no-submission promise")
    learning_policy = (ROOT / "LEARNING_POLICY.md").read_text(encoding="utf-8")
    record(errors, "does not retrain model weights" in learning_policy, "learning policy overclaims retraining")
    record(errors, "does not transmit" in learning_policy, "learning policy lost transmission boundary")
    validate_release_automation(errors)

    link_count = validate_local_links(errors)
    block_quote_count, inline_quote_count = validate_long_quotes(errors)

    with tempfile.TemporaryDirectory(prefix="live-consultant-pycompile-") as temporary:
        compile_root = Path(temporary)
        scripts = list((PLUGIN / "scripts").glob("*.py"))
        scripts.extend((ROOT / "scripts").glob("*.py"))
        for script in sorted(scripts):
            try:
                py_compile.compile(
                    str(script),
                    cfile=str(compile_root / f"{script.name}.pyc"),
                    doraise=True,
                )
            except py_compile.PyCompileError as exc:
                errors.append(
                    f"Python compilation failed for {script.relative_to(ROOT)}: {exc.msg}"
                )

    coverage = subprocess.run(
        [sys.executable, str(PLUGIN / "scripts" / "verify_source_coverage.py")],
        text=True,
        capture_output=True,
    )
    if coverage.returncode != 0:
        errors.append(f"source coverage failed: {coverage.stdout}{coverage.stderr}")

    skill_assembly = subprocess.run(
        [sys.executable, str(PLUGIN / "scripts" / "verify_skill_assembly.py")],
        text=True,
        capture_output=True,
    )
    if skill_assembly.returncode != 0:
        errors.append(
            "skill assembly failed: "
            f"{skill_assembly.stdout}{skill_assembly.stderr}"
        )

    knowledge_access = subprocess.run(
        [sys.executable, str(PLUGIN / "scripts" / "verify_knowledge_access.py")],
        text=True,
        capture_output=True,
    )
    if knowledge_access.returncode != 0:
        errors.append(
            "knowledge access failed: "
            f"{knowledge_access.stdout}{knowledge_access.stderr}"
        )

    routing_selftest = subprocess.run(
        [sys.executable, str(PLUGIN / "scripts" / "skill_routing_selftest.py")],
        text=True,
        capture_output=True,
    )
    if routing_selftest.returncode != 0:
        errors.append(
            "skill routing self-test failed: "
            f"{routing_selftest.stdout}{routing_selftest.stderr}"
        )

    mutation_selftest = subprocess.run(
        [sys.executable, str(PLUGIN / "scripts" / "release_mutation_selftest.py")],
        text=True,
        capture_output=True,
    )
    if mutation_selftest.returncode != 0:
        errors.append(
            "release mutation self-test failed: "
            f"{mutation_selftest.stdout}{mutation_selftest.stderr}"
        )

    learning_selftest = subprocess.run(
        [sys.executable, str(PLUGIN / "scripts" / "learning_loop_selftest.py")],
        text=True,
        capture_output=True,
    )
    if learning_selftest.returncode != 0:
        errors.append(
            "learning loop self-test failed: "
            f"{learning_selftest.stdout}{learning_selftest.stderr}"
        )

    foundation_integrity = subprocess.run(
        [sys.executable, str(PLUGIN / "scripts" / "verify_foundation_integrity.py")],
        text=True,
        capture_output=True,
    )
    if foundation_integrity.returncode != 0:
        errors.append(
            "foundation integrity failed: "
            f"{foundation_integrity.stdout}{foundation_integrity.stderr}"
        )

    release_metadata_selftest = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "release_metadata_selftest.py")],
        text=True,
        capture_output=True,
    )
    if release_metadata_selftest.returncode != 0:
        errors.append(
            "release metadata self-test failed: "
            f"{release_metadata_selftest.stdout}{release_metadata_selftest.stderr}"
        )

    summary = {
        "errors": errors,
        "foundation_integrity": foundation_integrity.stdout.strip(),
        "files": files,
        "local_links_checked": link_count,
        "block_quotes_checked": block_quote_count,
        "inline_case_quotes_checked": inline_quote_count,
        "learning_selftest": learning_selftest.stdout.strip(),
        "knowledge_access": knowledge_access.stdout.strip(),
        "release_mutation_selftest": mutation_selftest.stdout.strip(),
        "release_metadata_selftest": release_metadata_selftest.stdout.strip(),
        "skills": skill_count,
        "skill_assembly": skill_assembly.stdout.strip(),
        "skill_routing_selftest": routing_selftest.stdout.strip(),
        "source_coverage": coverage.stdout.strip(),
        "version": version,
        "version_transition": version_transition,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
