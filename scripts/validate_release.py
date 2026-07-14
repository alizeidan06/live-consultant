#!/usr/bin/env python3
"""Validate the public Live Consultant marketplace without external packages."""

from __future__ import annotations

import json
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path


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
    Path(".github/workflows/validate.yml"),
    Path("CHANGELOG.md"),
    Path("CONTRIBUTING.md"),
    Path("LEARNING_POLICY.md"),
    Path("LICENSE"),
    Path("PRIVACY.md"),
    Path("README.md"),
    Path("SECURITY.md"),
    Path("TERMS.md"),
    Path("plugins/live-consultant/LICENSE"),
    Path("plugins/live-consultant/scripts/learning_loop.py"),
    Path("plugins/live-consultant/scripts/learning_loop_selftest.py"),
    Path("plugins/live-consultant/skills/improve-live-consultant/SKILL.md"),
    Path("plugins/live-consultant/skills/improve-live-consultant/references/foundation-invariants.md"),
    Path("plugins/live-consultant/skills/improve-live-consultant/references/learning-protocol.md"),
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


def record(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


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


def main() -> int:
    errors: list[str] = []

    for relative in sorted(REQUIRED_ROOT_FILES):
        record(errors, (ROOT / relative).is_file(), f"missing required file: {relative}")

    try:
        plugin_manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
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
        plugin_manifest = {}
        marketplace = {}
        marker = {}
        source_manifest = {}

    version = plugin_manifest.get("version", "")
    record(errors, plugin_manifest.get("name") == "live-consultant", "wrong plugin name")
    record(errors, bool(re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", version)), "plugin version is not release semver")
    record(errors, plugin_manifest.get("license") == "MIT", "plugin license is not MIT")
    record(errors, plugin_manifest.get("repository") == "https://github.com/alizeidan06/live-consultant", "wrong public repository URL")
    record(errors, marker.get("version") == version, "export marker version does not match plugin")
    record(errors, bool(re.fullmatch(r"[0-9a-f]{40}", marker.get("source_commit", ""))), "export marker lacks a source commit")
    changelog_text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    record(
        errors,
        bool(re.search(rf"(?m)^## {re.escape(version)}(?:\s+-|\s*$)", changelog_text)),
        "CHANGELOG.md has no entry for the plugin version",
    )

    interface = plugin_manifest.get("interface", {})
    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
        record(errors, bool(interface.get(field)), f"plugin interface field missing: {field}")
    prompts = interface.get("defaultPrompt", [])
    record(errors, isinstance(prompts, list) and 1 <= len(prompts) <= 3, "defaultPrompt must contain one to three entries")

    public_transform = source_manifest.get("public_release_transform", {})
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
    record(errors, skill_count == 23, f"expected 23 skills, found {skill_count}")

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

    privacy_text = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
    record(errors, "off by default" in privacy_text, "privacy policy lost local-learning opt-in")
    record(errors, "does not call GitHub" in privacy_text, "privacy policy lost no-submission promise")
    learning_policy = (ROOT / "LEARNING_POLICY.md").read_text(encoding="utf-8")
    record(errors, "does not retrain model weights" in learning_policy, "learning policy overclaims retraining")
    record(errors, "does not transmit" in learning_policy, "learning policy lost transmission boundary")
    workflow_text = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    record(errors, "pull_request_target" not in workflow_text, "privileged pull_request_target is forbidden")
    record(errors, "contents: read" in workflow_text, "validation workflow must remain read-only")

    link_count = validate_local_links(errors)
    block_quote_count, inline_quote_count = validate_long_quotes(errors)

    with tempfile.TemporaryDirectory(prefix="live-consultant-pycompile-") as temporary:
        compile_root = Path(temporary)
        for script in sorted((PLUGIN / "scripts").glob("*.py")):
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

    summary = {
        "errors": errors,
        "files": files,
        "local_links_checked": link_count,
        "block_quotes_checked": block_quote_count,
        "inline_case_quotes_checked": inline_quote_count,
        "learning_selftest": learning_selftest.stdout.strip(),
        "skills": skill_count,
        "source_coverage": coverage.stdout.strip(),
        "version": version,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
