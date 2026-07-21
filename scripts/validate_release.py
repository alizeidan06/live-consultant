#!/usr/bin/env python3
"""Validate the public Live Consultant marketplace without external packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

sys.dont_write_bytecode = True

from release_metadata import load_release_metadata, validate_version_transition


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "live-consultant"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
MARKER = ROOT / ".live-consultant-public-export.json"
MCP_ENDPOINT = "https://live-consultant.sifr.marketing/mcp"

REQUIRED_ROOT_FILES = {
    Path(".agents/plugins/marketplace.json"),
    Path(".github/CODEOWNERS"),
    Path(".github/ISSUE_TEMPLATE/config.yml"),
    Path(".github/ISSUE_TEMPLATE/learning.yml"),
    Path(".github/pull_request_template.md"),
    Path(".github/workflows/release.yml"),
    Path(".github/workflows/validate.yml"),
    Path("app/.well-known/openai-apps-challenge/route.js"),
    Path("app/[transport]/route.js"),
    Path("app/healthz/route.js"),
    Path("CHANGELOG.md"),
    Path("CONTRIBUTING.md"),
    Path("LEARNING_POLICY.md"),
    Path("LICENSE"),
    Path("OPENAI_REVIEW.md"),
    Path("lib/live-consultant-knowledge.js"),
    Path("lib/live-consultant-runtime.js"),
    Path("lib/live-consultant-tools.js"),
    Path("next.config.mjs"),
    Path("package-lock.json"),
    Path("package.json"),
    Path("PRIVACY.md"),
    Path("README.md"),
    Path("runtime/runtime-directives.json"),
    Path("scripts/release_metadata.py"),
    Path("scripts/release_metadata_selftest.py"),
    Path("tests/fixtures/tool-contract.v0.5.1.json"),
    Path("tests/fixtures/tool-contract.v0.6.0.json"),
    Path("tests/runtime.test.js"),
    Path("SECURITY.md"),
    Path("TERMS.md"),
    Path("plugins/live-consultant/LICENSE"),
    Path("plugins/live-consultant/.mcp.json"),
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
    Path("plugins/live-consultant/scripts/copy_continuity_selftest.py"),
    Path("plugins/live-consultant/skills/design-offer-funnel/references/sales-letter-continuity.md"),
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
    "actions/setup-node": "49933ea5288caeca8642d1e84afbd3f7d6820020",
    "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
}
ACTION_USE_PATTERN = re.compile(
    r"(?m)^\s*(?:-\s*)?uses:\s*(?P<action>[^@\s]+)@(?P<revision>[^\s#]+)"
)
ZERO_SHA_PATTERN = re.compile(r"^0{40}$")
LEGACY_TOOL_CONTRACT_SHA256 = (
    "b735cd0f2fafcf309e7cf88cda2efdabdd7f9e7b5f2f3dc6d7b5a849a177afdb"
)
V06_TOOL_CONTRACT_SHA256 = (
    "555d632d8680565071d606b011068efa57f8d9109f5b2093550f2020d627b8df"
)


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


def validate_action_pins(
    errors: list[str],
    workflow: Path,
    text: str,
    required_actions: set[str],
) -> None:
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
    for action in sorted(required_actions):
        record(
            errors,
            action in seen_actions,
            f"workflow lost required reviewed action: {workflow.relative_to(ROOT)} -> {action}",
        )


def validate_clean_package_first(errors: list[str], text: str) -> None:
    package_steps = list(
        re.finditer(
            r"(?m)^(?P<indent>[ \t]*)-[ \t]+name:[ \t]+Validate release package[ \t]*$",
            text,
        )
    )
    runtime_steps = list(
        re.finditer(
            r"(?m)^[ \t]*-[ \t]+name:[ \t]+Validate hosted MCP runtime[ \t]*$",
            text,
        )
    )
    setup_node_steps = list(
        re.finditer(
            r"(?m)^[ \t]*-[ \t]+uses:[ \t]+actions/setup-node@[^\s#]+",
            text,
        )
    )
    run_keys = list(
        re.finditer(
            r"(?m)^(?P<indent>[ \t]*)(?:-[ \t]+)?run[ \t]*:[ \t]*.*$",
            text,
        )
    )
    record(
        errors,
        len(package_steps) == 1 and len(runtime_steps) == 1,
        "validation workflow must contain exactly one clean-package step and one hosted-runtime step",
    )
    record(
        errors,
        len(setup_node_steps) == 1 and bool(run_keys),
        "validation workflow must contain one Node setup and at least one shell step",
    )
    if (
        len(package_steps) != 1
        or len(runtime_steps) != 1
        or len(setup_node_steps) != 1
        or not run_keys
    ):
        return

    package_step = package_steps[0]
    package_indent = package_step.group("indent")
    next_step = re.search(
        rf"(?m)^{re.escape(package_indent)}-[ \t]+(?:name|uses|run)[ \t]*:",
        text[package_step.end():],
    )
    package_end = (
        package_step.end() + next_step.start() if next_step is not None else len(text)
    )
    package_run_keys = [
        match
        for match in run_keys
        if package_step.start() < match.start() < package_end
        and len(match.group("indent")) > len(package_indent)
    ]
    record(
        errors,
        len(package_run_keys) == 1
        and run_keys[0].start() == package_run_keys[0].start()
        and runtime_steps[0].start() >= package_end
        and setup_node_steps[0].start() >= package_end,
        "clean-package validation must be the first shell step and run before Node setup",
    )


def validate_release_automation(errors: list[str]) -> None:
    validate_path = ROOT / ".github/workflows/validate.yml"
    release_path = ROOT / ".github/workflows/release.yml"
    if not validate_path.is_file() or not release_path.is_file():
        return

    validate_text = validate_path.read_text(encoding="utf-8")
    release_text = release_path.read_text(encoding="utf-8")
    validate_clean_package_first(errors, validate_text)
    validate_action_pins(
        errors,
        validate_path,
        validate_text,
        {"actions/checkout", "actions/setup-node", "actions/setup-python"},
    )
    validate_action_pins(
        errors,
        release_path,
        release_text,
        {"actions/checkout", "actions/setup-python"},
    )

    record(errors, "pull_request_target" not in validate_text, "privileged pull_request_target is forbidden")
    record(errors, "contents: read" in validate_text, "validation workflow must remain read-only")
    for required in (
        "fetch-depth: 0",
        "persist-credentials: false",
        'node-version: "20"',
        "npm ci",
        "npm run check",
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
        mcp_manifest = json.loads(
            (PLUGIN / ".mcp.json").read_text(encoding="utf-8")
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
        runtime_package = json.loads(
            (ROOT / "package.json").read_text(encoding="utf-8")
        )
        runtime_lock = json.loads(
            (ROOT / "package-lock.json").read_text(encoding="utf-8")
        )
        runtime_directives = json.loads(
            (ROOT / "runtime/runtime-directives.json").read_text(encoding="utf-8")
        )
        legacy_tool_contract = json.loads(
            (ROOT / "tests/fixtures/tool-contract.v0.5.1.json").read_text(
                encoding="utf-8"
            )
        )
        v06_tool_contract = json.loads(
            (ROOT / "tests/fixtures/tool-contract.v0.6.0.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"manifest read failed: {exc}")
        plugin_manifest_text = "{}"
        plugin_manifest = {}
        mcp_manifest = {}
        marketplace = {}
        marker = {}
        source_manifest = {}
        runtime_package = {}
        runtime_lock = {}
        runtime_directives = {}
        legacy_tool_contract = []
        v06_tool_contract = []

    version = plugin_manifest.get("version", "")
    record(errors, plugin_manifest.get("name") == "live-consultant", "wrong plugin name")
    record(errors, bool(re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", version)), "plugin version is not release semver")
    record(errors, plugin_manifest.get("license") == "MIT", "plugin license is not MIT")
    record(errors, plugin_manifest.get("repository") == "https://github.com/alizeidan06/live-consultant", "wrong public repository URL")
    record(
        errors,
        plugin_manifest.get("mcpServers") == "./.mcp.json",
        "plugin manifest does not declare the MCP companion",
    )
    mcp_servers = mcp_manifest.get("mcpServers", {})
    record(
        errors,
        set(mcp_servers) == {"live-consultant"},
        "MCP companion must declare exactly the live-consultant server",
    )
    live_mcp = mcp_servers.get("live-consultant", {})
    record(
        errors,
        live_mcp == {"type": "http", "url": MCP_ENDPOINT},
        "Live Consultant MCP configuration changed unexpectedly",
    )
    parsed_mcp_endpoint = urlparse(live_mcp.get("url", ""))
    record(errors, parsed_mcp_endpoint.scheme == "https", "MCP endpoint must use HTTPS")
    record(
        errors,
        parsed_mcp_endpoint.hostname == "live-consultant.sifr.marketing",
        "MCP endpoint must stay on the reviewed SIFR subdomain",
    )
    record(errors, parsed_mcp_endpoint.path == "/mcp", "MCP endpoint path must be /mcp")

    expected_runtime_dependencies = {
        "@modelcontextprotocol/sdk": "1.26.0",
        "@opentelemetry/api": "1.9.1",
        "mcp-handler": "1.1.0",
        "next": "16.2.10",
        "react": "19.2.7",
        "react-dom": "19.2.7",
        "zod": "3.25.76",
    }
    expected_runtime_overrides = {"postcss": "8.5.19"}
    record(errors, runtime_package.get("private") is True, "hosted runtime must remain private")
    record(
        errors,
        runtime_package.get("engines", {}).get("node") == ">=20.9.0",
        "hosted runtime Node floor changed unexpectedly",
    )
    record(
        errors,
        runtime_package.get("dependencies") == expected_runtime_dependencies,
        "hosted runtime dependencies are not exactly pinned",
    )
    record(
        errors,
        runtime_package.get("overrides") == expected_runtime_overrides,
        "hosted runtime security overrides are not exactly pinned",
    )
    runtime_scripts = runtime_package.get("scripts", {})
    record(
        errors,
        runtime_scripts.get("test")
        == "node --test --test-force-exit tests/*.test.js",
        "hosted runtime test command changed unexpectedly",
    )
    record(
        errors,
        runtime_scripts.get("build") == "next build",
        "hosted runtime build command changed",
    )
    record(
        errors,
        runtime_scripts.get("check") == "npm test && npm run build",
        "hosted runtime combined check changed",
    )
    record(
        errors,
        runtime_lock.get("lockfileVersion") == 3,
        "package lock must use lockfile version 3",
    )
    lock_root = runtime_lock.get("packages", {}).get("", {})
    record(
        errors,
        lock_root.get("dependencies") == expected_runtime_dependencies,
        "package lock root dependencies do not match package.json",
    )
    record(
        errors,
        runtime_lock.get("packages", {})
        .get("node_modules/@opentelemetry/api", {})
        .get("version")
        == expected_runtime_dependencies["@opentelemetry/api"],
        "package lock did not resolve the pinned OpenTelemetry API",
    )
    record(
        errors,
        runtime_lock.get("packages", {})
        .get("node_modules/postcss", {})
        .get("version")
        == expected_runtime_overrides["postcss"],
        "package lock did not resolve the pinned PostCSS security override",
    )

    runtime_tools_text = (ROOT / "lib/live-consultant-tools.js").read_text(
        encoding="utf-8"
    )
    runtime_knowledge_text = (ROOT / "lib/live-consultant-knowledge.js").read_text(
        encoding="utf-8"
    )
    runtime_module_text = (ROOT / "lib/live-consultant-runtime.js").read_text(
        encoding="utf-8"
    )
    runtime_route_text = (ROOT / "app/[transport]/route.js").read_text(
        encoding="utf-8"
    )
    challenge_route_text = (
        ROOT / "app/.well-known/openai-apps-challenge/route.js"
    ).read_text(encoding="utf-8")
    expected_tools = {
        "route_consultation",
        "load_knowledge_bundle",
        "live_consultant_status",
        "start_live_consultation",
        "load_live_consultant_bundle",
    }
    canonical_contract = lambda value: json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    legacy_contract_digest = hashlib.sha256(
        canonical_contract(legacy_tool_contract)
    ).hexdigest()
    v06_contract_digest = hashlib.sha256(
        canonical_contract(v06_tool_contract)
    ).hexdigest()
    record(
        errors,
        legacy_contract_digest == LEGACY_TOOL_CONTRACT_SHA256,
        "the immutable v0.5.1 legacy tool contract fixture changed",
    )
    record(
        errors,
        v06_contract_digest == V06_TOOL_CONTRACT_SHA256,
        "the permanent v0.6 hosted tool contract fixture changed",
    )
    record(
        errors,
        {tool.get("name") for tool in legacy_tool_contract if isinstance(tool, dict)}
        == {
            "route_consultation",
            "load_knowledge_bundle",
            "live_consultant_status",
        },
        "the v0.5.1 fixture does not contain exactly the three legacy tools",
    )
    record(
        errors,
        {tool.get("name") for tool in v06_tool_contract if isinstance(tool, dict)}
        == expected_tools,
        "the v0.6 fixture does not contain exactly the five permanent tools",
    )
    record(
        errors,
        runtime_tools_text.count("server.registerTool(") == len(expected_tools),
        "hosted runtime must expose exactly five tools",
    )
    for tool_name in sorted(expected_tools):
        record(
            errors,
            f'"{tool_name}"' in runtime_tools_text,
            f"hosted runtime tool missing: {tool_name}",
        )
    record(
        errors,
        "./live-consultant-runtime.js" in runtime_tools_text,
        "hosted tools do not import the v0.6 runtime contract",
    )
    runtime_directives_object = (
        runtime_directives if isinstance(runtime_directives, dict) else {}
    )
    record(
        errors,
        isinstance(runtime_directives, dict) and bool(runtime_directives),
        "hosted runtime directives must be a non-empty JSON object",
    )
    expected_directive_fields = {
        "schema_version",
        "contract_version",
        "directives_version",
        "minimum_plugin_version",
        "content",
    }
    record(
        errors,
        isinstance(runtime_directives, dict)
        and set(runtime_directives_object) == expected_directive_fields,
        "hosted runtime directives fields changed unexpectedly",
    )
    record(
        errors,
        runtime_directives_object.get("schema_version") == 1,
        "hosted runtime directives schema_version must be 1",
    )
    for field in (
        "contract_version",
        "directives_version",
        "minimum_plugin_version",
    ):
        value = runtime_directives_object.get(field)
        record(
            errors,
            isinstance(value, str)
            and bool(
                re.fullmatch(
                    r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)",
                    value,
                )
            ),
            f"hosted runtime directives {field} must be release semver",
        )
    record(
        errors,
        runtime_directives_object.get("contract_version") == "1.0.0",
        "hosted runtime contract version must remain 1.0.0",
    )
    record(
        errors,
        runtime_directives_object.get("minimum_plugin_version") == "0.6.0",
        "hosted runtime minimum plugin version must remain 0.6.0",
    )
    directive_content = runtime_directives_object.get("content")
    record(
        errors,
        isinstance(directive_content, str) and bool(directive_content.strip()),
        "hosted runtime directives content must be a non-empty string",
    )
    for invariant in (
        "frameworks backstage",
        "one shared causal belief spine",
        "then branch deliberately",
        "Retain visuals or motion when",
        "shorter, visual, and technical countercases",
        "hero offer for ready buyers",
        "without repeating offer blocks",
    ):
        record(
            errors,
            isinstance(directive_content, str) and invariant in directive_content,
            f"hosted runtime directives lost copy-continuity invariant: {invariant}",
        )
    for invariant in (
        "readOnlyHint: true",
        "destructiveHint: false",
        "idempotentHint: true",
        "openWorldHint: false",
        "outputSchema: ROUTE_OUTPUT_SCHEMA",
        "outputSchema: BUNDLE_OUTPUT_SCHEMA",
        "outputSchema: STATUS_OUTPUT_SCHEMA",
        "business_context",
        "Do not send conversation history",
    ):
        record(
            errors,
            invariant in runtime_tools_text,
            f"hosted tool annotation missing: {invariant}",
        )
    for invariant in (
        "disableSse: true",
        "verboseLogs: false",
        "redisUrl: undefined",
    ):
        record(
            errors,
            invariant in runtime_route_text,
            f"hosted transport invariant missing: {invariant}",
        )
    record(
        errors,
        "OPENAI_APPS_CHALLENGE" in challenge_route_text,
        "OpenAI domain challenge route lost its environment-backed value",
    )
    runtime_javascript = {
        path.relative_to(ROOT): path.read_text(encoding="utf-8")
        for path in sorted(
            {
                *(ROOT / "lib").glob("*.js"),
                *(ROOT / "app").rglob("*.js"),
            }
        )
    }
    for relative, javascript in runtime_javascript.items():
        record(
            errors,
            "fetch(" not in javascript,
            f"hosted runtime may not fetch external data: {relative}",
        )
        record(
            errors,
            "console." not in javascript,
            f"hosted runtime may not log prompts: {relative}",
        )
    record(
        errors,
        "runtime-directives.json" in runtime_module_text,
        "hosted runtime module does not load the versioned directives",
    )
    for invariant in (
        "createHmac",
        "LIVE_CONSULTANT_TOKEN_SECRET",
        "timingSafeEqual",
        "RUNTIME_NOT_READY: hosted token authentication is not configured",
    ):
        record(
            errors,
            invariant in runtime_module_text,
            f"hosted token authentication invariant missing: {invariant}",
        )
    health_route_text = (ROOT / "app/healthz/route.js").read_text(encoding="utf-8")
    record(
        errors,
        "assertLiveConsultantRuntimeReady" in health_route_text,
        "hosted health route does not fail closed on runtime authentication",
    )
    for invariant in (
        "safeTarget",
        "Symbolic links are not allowed",
        "complete_recursive_markdown_plus_declared_files",
        'persistence: "none"',
        "prompt_logging: false",
    ):
        record(
            errors,
            invariant in runtime_knowledge_text,
            f"hosted knowledge invariant missing: {invariant}",
        )
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
    privacy_words = " ".join(privacy_text.split())
    record(errors, "off by default" in privacy_text, "privacy policy lost local-learning opt-in")
    record(errors, "does not call GitHub" in privacy_text, "privacy policy lost no-submission promise")
    record(
        errors,
        "does not require a Live Consultant account" in privacy_words,
        "privacy policy lost hosted account boundary",
    )
    record(
        errors,
        "intentionally persist tool arguments" in privacy_words,
        "privacy policy lost hosted persistence boundary",
    )
    learning_policy = (ROOT / "LEARNING_POLICY.md").read_text(encoding="utf-8")
    learning_policy_words = " ".join(learning_policy.split())
    record(errors, "does not retrain model weights" in learning_policy, "learning policy overclaims retraining")
    record(
        errors,
        "does not submit learning reports automatically" in learning_policy_words,
        "learning policy lost automatic-submission boundary",
    )
    record(
        errors,
        "does not turn those arguments into learning records" in learning_policy_words,
        "learning policy lost hosted learning boundary",
    )
    reviewer_packet = (ROOT / "OPENAI_REVIEW.md").read_text(encoding="utf-8")
    try:
        positive_section = reviewer_packet.split(
            "## Five positive reviewer tests", 1
        )[1].split("## Three negative reviewer tests", 1)[0]
        negative_section = reviewer_packet.split(
            "## Three negative reviewer tests", 1
        )[1].split("## Submission notes", 1)[0]
    except IndexError:
        positive_section = ""
        negative_section = ""
    record(
        errors,
        len(re.findall(r"(?m)^\d+\. \*\*", positive_section)) == 5,
        "OpenAI reviewer packet must contain exactly five positive tests",
    )
    record(
        errors,
        len(re.findall(r"(?m)^\d+\. \*\*", negative_section)) == 3,
        "OpenAI reviewer packet must contain exactly three negative tests",
    )
    for invariant in (
        "`connect_domains`: `[]`",
        "`resource_domains`: `[]`",
        "https://github.com/alizeidan06/live-consultant/issues",
    ):
        record(
            errors,
            invariant in reviewer_packet,
            f"OpenAI reviewer packet lost declaration: {invariant}",
        )
    assembly_protocol = (
        PLUGIN
        / "skills/founder-business-consultant/references/skill-assembly-protocol.md"
    ).read_text(encoding="utf-8")
    assembly_protocol_words = " ".join(assembly_protocol.split())
    for invariant in (
        "start_live_consultation",
        "load_live_consultant_bundle",
        "route_consultation",
        "load_knowledge_bundle",
        "the hosted load is complete when the response value is `null`",
        "every selected bundle page has been read and `next_cursor` is `null`",
        "Older task registries retain the unchanged legacy",
        "hosted tools are absent, unavailable, or fail closed, fall back to the complete bundled package",
        "restart with `start_live_consultation`, and load from the first page",
    ):
        record(
            errors,
            invariant in assembly_protocol_words,
            f"skill assembly lost hosted-first invariant: {invariant}",
        )
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

    copy_continuity_selftest = subprocess.run(
        [sys.executable, str(PLUGIN / "scripts" / "copy_continuity_selftest.py")],
        text=True,
        capture_output=True,
    )
    if copy_continuity_selftest.returncode != 0:
        errors.append(
            "copy continuity self-test failed: "
            f"{copy_continuity_selftest.stdout}{copy_continuity_selftest.stderr}"
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
        "copy_continuity_selftest": copy_continuity_selftest.stdout.strip(),
        "knowledge_access": knowledge_access.stdout.strip(),
        "mcp_endpoint": MCP_ENDPOINT,
        "runtime_tools": sorted(expected_tools),
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
