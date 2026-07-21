#!/usr/bin/env python3
"""Privacy-preserving, project-local learning loop for Live Consultant."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional


SCHEMA_VERSION = "1.0"
LEARNING_RELATIVE = Path(".live-consultant") / "learning"
EMPTY_EVENT_HMAC = "0" * 64
FOUNDATION_IDS = {f"LC-F{number:02d}" for number in range(1, 13)}
PLUGIN_SKILL_IDS = {
    "analyze-business-meeting",
    "audit-business",
    "build-business-operations",
    "design-offer-funnel",
    "founder-business-consultant",
    "founder-playbook-100m-leads",
    "founder-playbook-100m-offers",
    "founder-playbook-blue-ocean",
    "founder-playbook-crossing-the-chasm",
    "founder-playbook-diagnose",
    "founder-playbook-four-steps",
    "founder-playbook-influence",
    "founder-playbook-lean-startup",
    "founder-playbook-made-to-stick",
    "founder-playbook-mom-test",
    "founder-playbook-monetizing-innovation",
    "founder-playbook-obviously-awesome",
    "founder-playbook-spin-selling",
    "founder-playbook-storybrand",
    "founder-playbook-traction",
    "improve-live-consultant",
    "plan-meta-ads",
    "optimize-inventory-cash-flow",
    "reason-business-decision",
    "sell-like-crazy",
    "validate-business-idea",
}
DETECTION_SOURCES = {
    "self_check",
    "user_correction",
    "test_failure",
    "observed_outcome",
    "maintainer_review",
}
FAILURE_KINDS = {
    "fact",
    "access_claim",
    "arithmetic",
    "reasoning",
    "framework_routing",
    "scope",
    "missing_context",
    "ideation_dilution",
    "execution_gate",
    "voice",
    "tooling",
    "preference",
}
SEVERITIES = {"low", "medium", "high", "critical"}
CLAIM_TYPES = {
    "verified_fact",
    "reported_fact",
    "hypothesis",
    "preference",
    "constraint",
    "unknown",
}
EVIDENCE_KINDS = {
    "primary_artifact",
    "authoritative_source",
    "measured_outcome",
    "deterministic_reproduction",
    "public_research",
}
LINEAGE_PATTERN = re.compile(r"lin-[0-9a-f]{16}")
ROOT_CAUSES = {
    "missing_input",
    "stale_fact",
    "bad_inference",
    "arithmetic_error",
    "wrong_route",
    "overgeneralization",
    "foundation_miss",
    "preference_misread",
    "other",
}
FOUNDATION_EFFECTS = {"strengthen", "clarify", "scope", "contradict"}
VERIFICATION_RESULTS = {"pending", "pass", "fail"}
CONFIDENCE_LEVELS = {"low", "medium", "high"}
PROMOTION_TARGETS = {"local-rule", "core-proposal", "reject"}

FORBIDDEN_KEYS = {
    "raw_prompt",
    "raw_response",
    "prompt",
    "response",
    "transcript",
    "customer_name",
    "customer_names",
    "email",
    "phone",
    "account_id",
    "ip_address",
    "private_url",
    "local_path",
    "analytics_id",
    "crm_export",
    "attachment",
    "attachments",
}

SECRET_PATTERNS = {
    "private key": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    "GitHub token": re.compile(r"\bgh[opusr]_[A-Za-z0-9_]{16,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Stripe-style key": re.compile(
        r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{12,}\b"
    ),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}\b"),
    "JWT": re.compile(
        r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"
    ),
    "assigned secret": re.compile(
        r"(?i)\b(?:api[_ -]?key|password|secret|access[_ -]?token)\s*[:=]\s*\S+"
    ),
}

INJECTION_PATTERNS = {
    "instruction override": re.compile(
        r"(?i)\bignore\s+(?:all|any|the|previous|prior)\s+(?:instructions|rules|messages)\b"
    ),
    "system prompt reference": re.compile(r"(?i)\b(?:system prompt|developer message)\b"),
    "role override": re.compile(r"(?i)\b(?:act as|you are)\s+(?:chatgpt|the system|an unrestricted)\b"),
    "active content": re.compile(r"(?i)(?:<script\b|javascript:|data:text/html)"),
}

REDACTION_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "phone": re.compile(r"(?<!\w)(?:\+?\d[\d ().-]{7,}\d)(?!\w)"),
    "local path": re.compile(
        r"(?:/(?:Users|home)/[^\s]+|[A-Za-z]:\\(?:Users|Documents and Settings)\\[^\s]+)"
    ),
    "URL": re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>()]+"),
    "account ID": re.compile(
        r"(?i)\b(?:acct|account|org|customer|client|user|workspace|project)_[A-Za-z0-9-]{6,}\b"
    ),
    "named customer": re.compile(
        r"\b(?i:customer|client|company|contact)\s+(?:named\s+)?"
        r"[A-Z][A-Za-z0-9&.'-]*(?:\s+[A-Z][A-Za-z0-9&.'-]*){0,3}"
    ),
    "proper name": re.compile(
        r"\b[A-Z][A-Za-z0-9&.'-]+(?:\s+[A-Z][A-Za-z0-9&.'-]+){1,3}\b"
    ),
}


class LearningError(ValueError):
    """Raised for a rejected learning operation."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def safe_workspace(raw: Path) -> Path:
    if raw.is_symlink():
        raise LearningError("workspace symlinks are not accepted")
    try:
        resolved = raw.resolve(strict=True)
    except FileNotFoundError as exc:
        raise LearningError(f"workspace does not exist: {raw}") from exc
    if not resolved.is_dir():
        raise LearningError("workspace must be a directory")
    return resolved


def learning_root(workspace: Path) -> Path:
    root = workspace / LEARNING_RELATIVE
    if root.exists() and root.is_symlink():
        raise LearningError("learning directory symlinks are not accepted")
    resolved_parent = root.parent.resolve()
    try:
        resolved_parent.relative_to(workspace)
    except ValueError as exc:
        raise LearningError("learning directory escapes the workspace") from exc
    return root


def ensure_inside(root: Path, path: Path) -> None:
    try:
        lexical = path.relative_to(root)
    except ValueError as exc:
        raise LearningError(f"path escapes learning directory: {path}") from exc
    current = root
    for part in lexical.parts:
        current /= part
        if current.is_symlink():
            raise LearningError(f"symlink rejected: {current.name}")
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise LearningError(f"path escapes learning directory: {path}") from exc
    if path.exists() and path.is_symlink():
        raise LearningError(f"symlink rejected: {path.name}")


def set_private_permissions(path: Path, directory: bool = False) -> None:
    try:
        path.chmod(0o700 if directory else 0o600)
    except OSError:
        pass


def make_private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    set_private_permissions(path, directory=True)


def write_private(path: Path, content: str, root: Path, overwrite: bool = True) -> None:
    ensure_inside(root, path)
    make_private_directory(path.parent)
    if path.exists() and not overwrite:
        raise LearningError(f"refusing to overwrite existing file: {path.name}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        set_private_permissions(temporary)
        os.replace(temporary, path)
        set_private_permissions(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def read_private(path: Path, root: Path, label: str) -> str:
    ensure_inside(root, path)
    if not path.is_file():
        raise LearningError(f"{label} is missing")
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LearningError(f"could not read {label}: {exc}") from exc


def integrity_key(root: Path) -> bytes:
    path = root / "integrity.key"
    text = read_private(path, root, "learning integrity key").strip()
    if not re.fullmatch(r"[0-9a-f]{64}", text):
        raise LearningError("learning integrity key is invalid")
    return bytes.fromhex(text)


def sign_payload(root: Path, payload: dict[str, Any]) -> str:
    return hmac.new(
        integrity_key(root),
        canonical_json(payload).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_signature(root: Path, payload: dict[str, Any], signature: Any, label: str) -> None:
    if not isinstance(signature, str) or not re.fullmatch(r"[0-9a-f]{64}", signature):
        raise LearningError(f"{label} signature is invalid")
    if not hmac.compare_digest(sign_payload(root, payload), signature):
        raise LearningError(f"{label} integrity check failed")


def event_head_payload(sequence: int, last_hmac: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "sequence": sequence,
        "last_hmac": last_hmac,
    }


def write_event_head(root: Path, sequence: int, last_hmac: str) -> None:
    payload = event_head_payload(sequence, last_hmac)
    head = {**payload, "integrity_hmac": sign_payload(root, payload)}
    write_private(
        root / "events.head.json",
        json.dumps(head, indent=2, sort_keys=True) + "\n",
        root,
    )


def read_event_head(root: Path) -> dict[str, Any]:
    path = root / "events.head.json"
    try:
        head = json.loads(read_private(path, root, "learning event head"))
    except json.JSONDecodeError as exc:
        raise LearningError("learning event head is invalid JSON") from exc
    expected = {"schema_version", "sequence", "last_hmac", "integrity_hmac"}
    if not isinstance(head, dict) or set(head) != expected:
        raise LearningError("learning event head has an unexpected schema")
    if head.get("schema_version") != SCHEMA_VERSION:
        raise LearningError("learning event head has an unsupported schema version")
    if not isinstance(head.get("sequence"), int) or isinstance(
        head.get("sequence"), bool
    ) or head["sequence"] < 0:
        raise LearningError("learning event head sequence is invalid")
    if not isinstance(head.get("last_hmac"), str) or not re.fullmatch(
        r"[0-9a-f]{64}", head["last_hmac"]
    ):
        raise LearningError("learning event head digest is invalid")
    unsigned = {key: value for key, value in head.items() if key != "integrity_hmac"}
    verify_signature(root, unsigned, head.get("integrity_hmac"), "learning event head")
    return head


def append_event(root: Path, event: dict[str, Any]) -> None:
    read_events(root)
    head = read_event_head(root)
    unsigned = {
        **event,
        "sequence": head["sequence"] + 1,
        "previous_hmac": head["last_hmac"],
    }
    event = {**unsigned, "integrity_hmac": sign_payload(root, unsigned)}
    path = root / "events.jsonl"
    ensure_inside(root, path)
    make_private_directory(path.parent)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        handle.write(canonical_json(event) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    set_private_permissions(path)
    write_event_head(root, event["sequence"], event["integrity_hmac"])


def initialize_store(workspace: Path, enabled: bool) -> Path:
    root = learning_root(workspace)
    make_private_directory(root)
    for child in ("candidates", "proposals", "previews", "contributions"):
        child_path = root / child
        ensure_inside(root, child_path)
        make_private_directory(child_path)
    key_path = root / "integrity.key"
    ensure_inside(root, key_path)
    if not key_path.exists():
        write_private(key_path, secrets.token_hex(32) + "\n", root, overwrite=False)
    else:
        integrity_key(root)
    settings = {
        "schema_version": SCHEMA_VERSION,
        "local_learning_enabled": enabled,
        "telemetry_enabled": False,
        "automatic_public_submission": False,
        "scope": "this-project-only",
    }
    settings["integrity_hmac"] = sign_payload(root, settings)
    write_private(
        root / "settings.json",
        json.dumps(settings, indent=2, sort_keys=True) + "\n",
        root,
    )
    ignore = "# Local learning can contain private business context.\n*\n!.gitignore\n"
    write_private(root / ".gitignore", ignore, root)
    if not (root / "events.jsonl").exists():
        write_private(root / "events.jsonl", "", root, overwrite=False)
    head_path = root / "events.head.json"
    if not head_path.exists():
        if read_private(root / "events.jsonl", root, "learning events").strip():
            raise LearningError("learning event head is missing for a non-empty ledger")
        write_event_head(root, 0, EMPTY_EVENT_HMAC)
    else:
        read_event_head(root)
    render_active_rules(root)
    return root


def read_settings(root: Path) -> dict[str, Any]:
    path = root / "settings.json"
    try:
        settings = json.loads(read_private(path, root, "learning settings"))
    except json.JSONDecodeError as exc:
        raise LearningError("learning settings are invalid JSON") from exc
    if set(settings) != {
        "schema_version",
        "local_learning_enabled",
        "telemetry_enabled",
        "automatic_public_submission",
        "scope",
        "integrity_hmac",
    }:
        raise LearningError("learning settings have an unexpected schema")
    signature = settings.pop("integrity_hmac")
    verify_signature(root, settings, signature, "learning settings")
    settings["integrity_hmac"] = signature
    if settings.get("telemetry_enabled") is not False:
        raise LearningError("telemetry must remain disabled")
    if settings.get("automatic_public_submission") is not False:
        raise LearningError("automatic public submission must remain disabled")
    return settings


def require_enabled(workspace: Path) -> Path:
    root = learning_root(workspace)
    settings = read_settings(root)
    if settings.get("local_learning_enabled") is not True:
        raise LearningError("local learning is disabled for this project")
    return root


def reject_forbidden_keys(value: Any, path: str = "input") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                raise LearningError(f"forbidden field: {path}.{key}")
            reject_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_forbidden_keys(child, f"{path}[{index}]")


def clean_text(
    value: Any,
    field: str,
    redactions: set[str],
    maximum: int = 800,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str):
        raise LearningError(f"{field} must be text")
    normalized = re.sub(r"\s+", " ", value).strip()
    if not normalized and not allow_empty:
        raise LearningError(f"{field} must not be empty")
    if len(normalized) > maximum:
        raise LearningError(f"{field} exceeds {maximum} characters")
    for label, pattern in SECRET_PATTERNS.items():
        if pattern.search(normalized):
            raise LearningError(f"{field} contains a forbidden {label}")
    for label, pattern in INJECTION_PATTERNS.items():
        if pattern.search(normalized):
            raise LearningError(f"{field} contains a forbidden {label}")
    for label, pattern in REDACTION_PATTERNS.items():
        replaced, count = pattern.subn(f"[REDACTED_{label.upper().replace(' ', '_')}]", normalized)
        if count:
            redactions.add(label)
            normalized = replaced
    return normalized


def clean_enum(value: Any, field: str, allowed: set[str]) -> str:
    if value not in allowed:
        raise LearningError(f"{field} must be one of: {', '.join(sorted(allowed))}")
    return str(value)


def clean_date(value: Any, field: str, allow_unknown: bool = False) -> str:
    if allow_unknown and value == "unknown":
        return "unknown"
    if not isinstance(value, str):
        raise LearningError(f"{field} must be an ISO date")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise LearningError(f"{field} must be an ISO date") from exc
    return value


def expect_keys(value: Any, field: str, expected: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LearningError(f"{field} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise LearningError(f"{field} schema mismatch; missing={missing}, extra={extra}")
    return value


def clean_text_list(
    value: Any,
    field: str,
    redactions: set[str],
    maximum_items: int,
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        raise LearningError(f"{field} must be a list")
    if not allow_empty and not value:
        raise LearningError(f"{field} must not be empty")
    if len(value) > maximum_items:
        raise LearningError(f"{field} has too many items")
    return [
        clean_text(item, f"{field}[{index}]", redactions, maximum=500)
        for index, item in enumerate(value)
    ]


def validate_evidence(
    value: Any, field: str, redactions: set[str], allow_empty: bool
) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise LearningError(f"{field} must be a list")
    if not allow_empty and not value:
        raise LearningError(f"{field} must not be empty")
    if len(value) > 8:
        raise LearningError(f"{field} has too many items")
    output: list[dict[str, str]] = []
    for index, raw in enumerate(value):
        item = expect_keys(
            raw,
            f"{field}[{index}]",
            {"lineage_id", "kind", "source_date", "scope", "supports"},
        )
        lineage_id = item["lineage_id"]
        if not isinstance(lineage_id, str) or not LINEAGE_PATTERN.fullmatch(
            lineage_id
        ):
            raise LearningError(
                f"{field}[{index}].lineage_id must match lin- plus 16 hex characters"
            )
        output.append(
            {
                "lineage_id": lineage_id,
                "kind": clean_enum(
                    item["kind"], f"{field}[{index}].kind", EVIDENCE_KINDS
                ),
                "source_date": clean_date(
                    item["source_date"],
                    f"{field}[{index}].source_date",
                    allow_unknown=True,
                ),
                "scope": clean_text(
                    item["scope"], f"{field}[{index}].scope", redactions, 300
                ),
                "supports": clean_text(
                    item["supports"], f"{field}[{index}].supports", redactions, 500
                ),
            }
        )
    return output


def validate_candidate(raw: Any) -> dict[str, Any]:
    reject_forbidden_keys(raw)
    data = expect_keys(
        raw,
        "input",
        {
            "plugin_version",
            "skill_ids",
            "foundation_ids",
            "detection",
            "context",
            "mistake",
            "evidence",
            "counterevidence",
            "root_cause",
            "proposal",
            "verification",
            "privacy",
            "governance",
        },
    )
    redactions: set[str] = set()

    plugin_version = clean_text(data["plugin_version"], "plugin_version", redactions, 40)
    if not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", plugin_version):
        raise LearningError("plugin_version must be release semver")

    skill_ids = clean_text_list(data["skill_ids"], "skill_ids", redactions, 12)
    if len(skill_ids) != len(set(skill_ids)):
        raise LearningError("skill_ids must not contain duplicates")
    if any(item not in PLUGIN_SKILL_IDS for item in skill_ids):
        raise LearningError("skill_ids contains an unknown Live Consultant skill")

    foundation_ids = data["foundation_ids"]
    if not isinstance(foundation_ids, list) or not foundation_ids:
        raise LearningError("foundation_ids must be a non-empty list")
    if len(foundation_ids) > len(FOUNDATION_IDS) or any(
        item not in FOUNDATION_IDS for item in foundation_ids
    ):
        raise LearningError("foundation_ids contains an unknown invariant")

    detection = expect_keys(
        data["detection"], "detection", {"source", "failure_kind", "severity"}
    )
    context = expect_keys(
        data["context"],
        "context",
        {"business_stage", "channel", "regulated", "scope"},
    )
    mistake = expect_keys(
        data["mistake"],
        "mistake",
        {"summary", "claim_type", "observed_effect"},
    )
    root_cause = expect_keys(
        data["root_cause"], "root_cause", {"code", "summary"}
    )
    proposal = expect_keys(
        data["proposal"],
        "proposal",
        {"rule", "applicability", "exceptions", "foundation_effect"},
    )
    verification = expect_keys(
        data["verification"],
        "verification",
        {
            "minimal_reproduction",
            "disconfirming_test",
            "regression_test_ids",
            "result",
        },
    )
    privacy = expect_keys(
        data["privacy"],
        "privacy",
        {
            "raw_transcript",
            "personal_data",
            "secrets",
            "confidential_business_data",
            "copyrighted_excerpt",
        },
    )
    if any(value is not False for value in privacy.values()):
        raise LearningError("privacy flags must all be false after redaction")
    governance = expect_keys(
        data["governance"], "governance", {"confidence", "review_due"}
    )

    candidate = {
        "schema_version": SCHEMA_VERSION,
        "plugin_version": plugin_version,
        "skill_ids": skill_ids,
        "foundation_ids": sorted(set(foundation_ids)),
        "detection": {
            "source": clean_enum(
                detection["source"], "detection.source", DETECTION_SOURCES
            ),
            "failure_kind": clean_enum(
                detection["failure_kind"],
                "detection.failure_kind",
                FAILURE_KINDS,
            ),
            "severity": clean_enum(
                detection["severity"], "detection.severity", SEVERITIES
            ),
        },
        "context": {
            "business_stage": clean_text(
                context["business_stage"], "context.business_stage", redactions, 100
            ),
            "channel": clean_text(
                context["channel"], "context.channel", redactions, 100
            ),
            "regulated": clean_enum(
                context["regulated"], "context.regulated", {"yes", "no", "unknown"}
            ),
            "scope": clean_text(context["scope"], "context.scope", redactions, 300),
        },
        "mistake": {
            "summary": clean_text(
                mistake["summary"], "mistake.summary", redactions, 500
            ),
            "claim_type": clean_enum(
                mistake["claim_type"], "mistake.claim_type", CLAIM_TYPES
            ),
            "observed_effect": clean_text(
                mistake["observed_effect"],
                "mistake.observed_effect",
                redactions,
                500,
            ),
        },
        "evidence": validate_evidence(
            data["evidence"], "evidence", redactions, allow_empty=False
        ),
        "counterevidence": validate_evidence(
            data["counterevidence"],
            "counterevidence",
            redactions,
            allow_empty=True,
        ),
        "root_cause": {
            "code": clean_enum(root_cause["code"], "root_cause.code", ROOT_CAUSES),
            "summary": clean_text(
                root_cause["summary"], "root_cause.summary", redactions, 500
            ),
        },
        "proposal": {
            "rule": clean_text(proposal["rule"], "proposal.rule", redactions, 600),
            "applicability": clean_text(
                proposal["applicability"],
                "proposal.applicability",
                redactions,
                500,
            ),
            "exceptions": clean_text_list(
                proposal["exceptions"],
                "proposal.exceptions",
                redactions,
                8,
                allow_empty=True,
            ),
            "foundation_effect": clean_enum(
                proposal["foundation_effect"],
                "proposal.foundation_effect",
                FOUNDATION_EFFECTS,
            ),
        },
        "verification": {
            "minimal_reproduction": clean_text_list(
                verification["minimal_reproduction"],
                "verification.minimal_reproduction",
                redactions,
                6,
            ),
            "disconfirming_test": clean_text(
                verification["disconfirming_test"],
                "verification.disconfirming_test",
                redactions,
                600,
            ),
            "regression_test_ids": clean_text_list(
                verification["regression_test_ids"],
                "verification.regression_test_ids",
                redactions,
                10,
            ),
            "result": clean_enum(
                verification["result"],
                "verification.result",
                VERIFICATION_RESULTS,
            ),
        },
        "privacy": {key: False for key in privacy},
        "governance": {
            "status": "candidate",
            "confidence": clean_enum(
                governance["confidence"],
                "governance.confidence",
                CONFIDENCE_LEVELS,
            ),
            "review_due": clean_date(
                governance["review_due"], "governance.review_due"
            ),
        },
        "redactions": sorted(redactions),
    }
    fingerprint_payload = {
        "plugin_version": candidate["plugin_version"],
        "skill_ids": candidate["skill_ids"],
        "foundation_ids": candidate["foundation_ids"],
        "failure_kind": candidate["detection"]["failure_kind"],
        "context": candidate["context"],
        "mistake": candidate["mistake"],
        "root_cause": candidate["root_cause"],
        "proposal": candidate["proposal"],
        "verification": candidate["verification"],
        "governance": candidate["governance"],
    }
    fingerprint = digest_text(canonical_json(fingerprint_payload))
    candidate["candidate_id"] = f"lc-{fingerprint[:16]}"
    candidate["fingerprint"] = fingerprint
    candidate["created_at"] = utc_now()
    return candidate


def read_json_input(value: str) -> Any:
    try:
        text = sys.stdin.read() if value == "-" else Path(value).read_text(encoding="utf-8")
        return json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        raise LearningError(f"could not read JSON input: {exc}") from exc


def validate_timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise LearningError(f"{field} must be a timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise LearningError(f"{field} must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise LearningError(f"{field} must include a timezone")
    return value


def validate_stored_event(
    event: Any, line_number: int, root: Path
) -> dict[str, Any]:
    label = f"events.jsonl line {line_number}"
    if not isinstance(event, dict):
        raise LearningError(f"{label} is not an object")
    if event.get("schema_version") != SCHEMA_VERSION:
        raise LearningError(f"{label} has an unsupported schema version")
    signature = event.get("integrity_hmac")
    unsigned = {key: value for key, value in event.items() if key != "integrity_hmac"}
    verify_signature(root, unsigned, signature, label)
    if not isinstance(event.get("sequence"), int) or isinstance(
        event.get("sequence"), bool
    ) or event["sequence"] < 1:
        raise LearningError(f"{label}.sequence is invalid")
    if not isinstance(event.get("previous_hmac"), str) or not re.fullmatch(
        r"[0-9a-f]{64}", event["previous_hmac"]
    ):
        raise LearningError(f"{label}.previous_hmac is invalid")
    event_type = event.get("event_type")
    validate_timestamp(event.get("created_at"), f"{label}.created_at")

    if event_type == "candidate":
        expected = {
            "schema_version",
            "event_type",
            "candidate_id",
            "created_at",
            "integrity_hmac",
            "sequence",
            "previous_hmac",
        }
        if set(event) != expected:
            raise LearningError(f"{label} has an unexpected schema")
        candidate_path(Path("."), event.get("candidate_id", ""))
        return event

    if event_type == "recurrence":
        expected = {
            "schema_version",
            "event_type",
            "candidate_id",
            "created_at",
            "evidence",
            "counterevidence",
            "reported_lineages",
            "integrity_hmac",
            "sequence",
            "previous_hmac",
        }
        if set(event) != expected:
            raise LearningError(f"{label} has an unexpected schema")
        candidate_path(Path("."), event.get("candidate_id", ""))
        redactions: set[str] = set()
        revalidated_evidence = validate_evidence(
            event["evidence"], f"{label}.evidence", redactions, allow_empty=True
        )
        revalidated_counterevidence = validate_evidence(
            event["counterevidence"],
            f"{label}.counterevidence",
            redactions,
            allow_empty=True,
        )
        if revalidated_evidence != event["evidence"] or (
            revalidated_counterevidence != event["counterevidence"]
        ):
            raise LearningError(f"{label} evidence failed integrity validation")
        reported_lineages = event["reported_lineages"]
        if (
            not isinstance(reported_lineages, list)
            or not reported_lineages
            or len(reported_lineages) != len(set(reported_lineages))
            or any(
                not isinstance(item, str) or not LINEAGE_PATTERN.fullmatch(item)
                for item in reported_lineages
            )
        ):
            raise LearningError(f"{label}.reported_lineages is invalid")
        stored_lineages = {
            item["lineage_id"]
            for item in event["evidence"] + event["counterevidence"]
        }
        if not stored_lineages.issubset(set(reported_lineages)):
            raise LearningError(f"{label} stored an unreported evidence lineage")
        return event

    if event_type == "decision":
        expected = {
            "schema_version",
            "event_type",
            "created_at",
            "candidate_id",
            "target",
            "decision",
            "evidence_summary",
            "regression_test",
            "countercase",
            "owner_approved",
            "independent_contexts",
            "measured_outcomes",
            "deterministic_reproduction",
            "public_safe",
            "redactions",
            "integrity_hmac",
            "sequence",
            "previous_hmac",
        }
        if set(event) != expected:
            raise LearningError(f"{label} has an unexpected schema")
        raw = {
            key: event[key]
            for key in expected
            if key
            not in {
                "schema_version",
                "event_type",
                "created_at",
                "redactions",
                "integrity_hmac",
                "sequence",
                "previous_hmac",
            }
        }
        revalidated = validate_promotion(raw)
        for key, value in revalidated.items():
            if key != "redactions" and event.get(key) != value:
                raise LearningError(f"{label}.{key} failed integrity validation")
        redactions = event.get("redactions")
        if (
            not isinstance(redactions, list)
            or len(redactions) != len(set(redactions))
            or any(item not in REDACTION_PATTERNS for item in redactions)
        ):
            raise LearningError(f"{label}.redactions is invalid")
        return event

    if event_type in {"preview", "contribution-finalized"}:
        expected = {
            "schema_version",
            "event_type",
            "candidate_id",
            "created_at",
            "digest",
        }
        if event_type == "contribution-finalized":
            expected.add("submitted")
        expected.add("integrity_hmac")
        expected.add("sequence")
        expected.add("previous_hmac")
        if set(event) != expected:
            raise LearningError(f"{label} has an unexpected schema")
        candidate_path(Path("."), event.get("candidate_id", ""))
        if not isinstance(event.get("digest"), str) or not re.fullmatch(
            r"[0-9a-f]{64}", event["digest"]
        ):
            raise LearningError(f"{label}.digest is invalid")
        if event_type == "contribution-finalized" and event.get("submitted") is not False:
            raise LearningError(f"{label}.submitted must remain false")
        return event

    raise LearningError(f"{label} has an unknown event type")


def read_events(root: Path) -> list[dict[str, Any]]:
    path = root / "events.jsonl"
    if not path.exists():
        raise LearningError("learning event ledger is missing")
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        read_private(path, root, "learning events").splitlines(), 1
    ):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LearningError(f"events.jsonl line {line_number} is invalid") from exc
        events.append(validate_stored_event(event, line_number, root))
    previous_hmac = EMPTY_EVENT_HMAC
    for expected_sequence, event in enumerate(events, 1):
        if event["sequence"] != expected_sequence:
            raise LearningError("learning event sequence is missing or reordered")
        if event["previous_hmac"] != previous_hmac:
            raise LearningError("learning event chain is broken")
        previous_hmac = event["integrity_hmac"]
    head = read_event_head(root)
    if head["sequence"] != len(events) or head["last_hmac"] != previous_hmac:
        raise LearningError("learning event ledger was truncated or does not match its head")
    return events


def candidate_path(root: Path, candidate_id: str) -> Path:
    if not re.fullmatch(r"lc-[0-9a-f]{16}", candidate_id):
        raise LearningError("invalid candidate ID")
    return root / "candidates" / f"{candidate_id}.json"


def load_candidate(root: Path, candidate_id: str) -> dict[str, Any]:
    path = candidate_path(root, candidate_id)
    try:
        candidate = json.loads(read_private(path, root, f"candidate {candidate_id}"))
    except json.JSONDecodeError as exc:
        raise LearningError(f"candidate is invalid JSON: {candidate_id}") from exc
    expected = {
        "schema_version",
        "plugin_version",
        "skill_ids",
        "foundation_ids",
        "detection",
        "context",
        "mistake",
        "evidence",
        "counterevidence",
        "root_cause",
        "proposal",
        "verification",
        "privacy",
        "governance",
        "redactions",
        "candidate_id",
        "fingerprint",
        "created_at",
        "integrity_hmac",
    }
    if not isinstance(candidate, dict) or set(candidate) != expected:
        raise LearningError(f"candidate has an unexpected schema: {candidate_id}")
    signature = candidate.get("integrity_hmac")
    unsigned = {
        key: value for key, value in candidate.items() if key != "integrity_hmac"
    }
    verify_signature(root, unsigned, signature, f"candidate {candidate_id}")
    validate_timestamp(candidate.get("created_at"), f"candidate {candidate_id}.created_at")
    redactions = candidate.get("redactions")
    if (
        not isinstance(redactions, list)
        or len(redactions) != len(set(redactions))
        or any(item not in REDACTION_PATTERNS for item in redactions)
    ):
        raise LearningError(f"candidate redactions are invalid: {candidate_id}")
    governance = candidate.get("governance")
    if not isinstance(governance, dict) or governance.get("status") != "candidate":
        raise LearningError(f"candidate governance is invalid: {candidate_id}")
    raw = {
        key: candidate[key]
        for key in (
            "plugin_version",
            "skill_ids",
            "foundation_ids",
            "detection",
            "context",
            "mistake",
            "evidence",
            "counterevidence",
            "root_cause",
            "proposal",
            "verification",
            "privacy",
        )
    }
    raw["governance"] = {
        "confidence": governance.get("confidence"),
        "review_due": governance.get("review_due"),
    }
    revalidated = validate_candidate(raw)
    if (
        candidate.get("schema_version") != SCHEMA_VERSION
        or candidate.get("candidate_id") != candidate_id
        or revalidated["candidate_id"] != candidate_id
        or candidate.get("fingerprint") != revalidated["fingerprint"]
    ):
        raise LearningError(f"candidate integrity check failed: {candidate_id}")
    return candidate


def dedupe_by_lineage(items: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: dict[str, dict[str, str]] = {}
    for item in items:
        deduped.setdefault(item["lineage_id"], item)
    return list(deduped.values())


def aggregate_candidate_evidence(
    root: Path, candidate: dict[str, Any]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    evidence = list(candidate["evidence"])
    counterevidence = list(candidate["counterevidence"])
    for event in read_events(root):
        if (
            event.get("event_type") == "recurrence"
            and event.get("candidate_id") == candidate["candidate_id"]
        ):
            evidence.extend(event["evidence"])
            counterevidence.extend(event["counterevidence"])
    return dedupe_by_lineage(evidence), dedupe_by_lineage(counterevidence)


def capture(workspace: Path, input_path: str) -> dict[str, Any]:
    root = require_enabled(workspace)
    candidate = validate_candidate(read_json_input(input_path))
    candidate["integrity_hmac"] = sign_payload(root, candidate)
    path = candidate_path(root, candidate["candidate_id"])
    event_type = "recurrence" if path.exists() else "candidate"
    new_evidence = list(candidate["evidence"])
    new_counterevidence = list(candidate["counterevidence"])
    duplicate_lineages: list[str] = []
    if not path.exists():
        write_private(
            path,
            json.dumps(candidate, indent=2, sort_keys=True) + "\n",
            root,
            overwrite=False,
        )
    else:
        existing = load_candidate(root, candidate["candidate_id"])
        existing_evidence, existing_counterevidence = aggregate_candidate_evidence(
            root, existing
        )
        existing_lineages = {
            item["lineage_id"]
            for item in existing_evidence + existing_counterevidence
        }
        reported = candidate["evidence"] + candidate["counterevidence"]
        duplicate_lineages = sorted(
            {
                item["lineage_id"]
                for item in reported
                if item["lineage_id"] in existing_lineages
            }
        )
        new_evidence = [
            item
            for item in candidate["evidence"]
            if item["lineage_id"] not in existing_lineages
        ]
        new_counterevidence = [
            item
            for item in candidate["counterevidence"]
            if item["lineage_id"] not in existing_lineages
        ]
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_type": event_type,
        "candidate_id": candidate["candidate_id"],
        "created_at": utc_now(),
    }
    if event_type == "recurrence":
        event.update(
            {
                "evidence": dedupe_by_lineage(new_evidence),
                "counterevidence": dedupe_by_lineage(new_counterevidence),
                "reported_lineages": sorted(
                    {
                        item["lineage_id"]
                        for item in candidate["evidence"]
                        + candidate["counterevidence"]
                    }
                ),
            }
        )
    append_event(root, event)
    return {
        "action": event_type,
        "candidate_id": candidate["candidate_id"],
        "redactions": candidate["redactions"],
        "stored_at": str(path.relative_to(workspace)),
        "new_evidence_lineages": sorted(
            {item["lineage_id"] for item in new_evidence + new_counterevidence}
        ),
        "duplicate_lineages": duplicate_lineages,
    }


def validate_promotion(raw: Any) -> dict[str, Any]:
    reject_forbidden_keys(raw)
    data = expect_keys(
        raw,
        "promotion",
        {
            "candidate_id",
            "target",
            "decision",
            "evidence_summary",
            "regression_test",
            "countercase",
            "owner_approved",
            "independent_contexts",
            "measured_outcomes",
            "deterministic_reproduction",
            "public_safe",
        },
    )
    redactions: set[str] = set()
    candidate_id = clean_text(data["candidate_id"], "candidate_id", redactions, 40)
    if not re.fullmatch(r"lc-[0-9a-f]{16}", candidate_id):
        raise LearningError("invalid candidate ID")
    for field in (
        "owner_approved",
        "deterministic_reproduction",
        "public_safe",
    ):
        if not isinstance(data[field], bool):
            raise LearningError(f"{field} must be boolean")
    for field in ("independent_contexts", "measured_outcomes"):
        if not isinstance(data[field], int) or isinstance(data[field], bool) or data[field] < 0:
            raise LearningError(f"{field} must be a non-negative integer")
    return {
        "candidate_id": candidate_id,
        "target": clean_enum(data["target"], "target", PROMOTION_TARGETS),
        "decision": clean_text(data["decision"], "decision", redactions, 500),
        "evidence_summary": clean_text(
            data["evidence_summary"], "evidence_summary", redactions, 600
        ),
        "regression_test": clean_text(
            data["regression_test"], "regression_test", redactions, 600
        ),
        "countercase": clean_text(data["countercase"], "countercase", redactions, 600),
        "owner_approved": data["owner_approved"],
        "independent_contexts": data["independent_contexts"],
        "measured_outcomes": data["measured_outcomes"],
        "deterministic_reproduction": data["deterministic_reproduction"],
        "public_safe": data["public_safe"],
        "redactions": sorted(redactions),
    }


def authoritative_fact_gate(
    candidate: dict[str, Any], evidence: list[dict[str, str]]
) -> bool:
    return candidate["detection"]["failure_kind"] == "fact" and any(
        item["kind"] == "authoritative_source" and item["source_date"] != "unknown"
        for item in evidence
    )


def deterministic_gate(
    candidate: dict[str, Any],
    decision: dict[str, Any],
    evidence: list[dict[str, str]],
) -> bool:
    return (
        decision["deterministic_reproduction"]
        and any(
            item["kind"] == "deterministic_reproduction"
            for item in evidence
        )
        and candidate["detection"]["failure_kind"]
        in {"access_claim", "arithmetic", "tooling"}
    )


def evidence_profile(evidence: list[dict[str, str]]) -> dict[str, int]:
    unique_lineages = {item["lineage_id"] for item in evidence}
    measured_lineages = {
        item["lineage_id"] for item in evidence if item["kind"] == "measured_outcome"
    }
    measured_scopes = {
        item["scope"].strip().lower()
        for item in evidence
        if item["kind"] == "measured_outcome"
    }
    return {
        "unique_lineages": len(unique_lineages),
        "measured_outcomes": len(measured_lineages),
        "measured_scopes": len(measured_scopes),
    }


def review_is_current(candidate: dict[str, Any]) -> bool:
    return date.fromisoformat(candidate["governance"]["review_due"]) >= date.today()


def check_promotion_gate(
    root: Path, candidate: dict[str, Any], decision: dict[str, Any]
) -> None:
    target = decision["target"]
    if target == "reject":
        return
    if not decision["owner_approved"]:
        raise LearningError("promotion requires explicit owner approval")
    if not review_is_current(candidate):
        raise LearningError("candidate review date has expired")
    if candidate["proposal"]["foundation_effect"] == "contradict":
        raise LearningError("a foundation contradiction cannot auto-promote")
    if candidate["verification"]["result"] != "pass":
        raise LearningError("promotion requires a passing verification result")

    source = candidate["detection"]["source"]
    evidence, _ = aggregate_candidate_evidence(root, candidate)
    profile = evidence_profile(evidence)
    if decision["measured_outcomes"] > profile["measured_outcomes"]:
        raise LearningError("promotion overstates recorded measured outcomes")
    if decision["independent_contexts"] > profile["unique_lineages"]:
        raise LearningError("promotion overstates recorded independent evidence")
    if decision["deterministic_reproduction"] and not any(
        item["kind"] == "deterministic_reproduction"
        for item in evidence
    ):
        raise LearningError("promotion claims an unrecorded deterministic reproduction")
    local_evidence = (
        source in {"user_correction", "maintainer_review"}
        or profile["measured_outcomes"] >= 1
        or deterministic_gate(candidate, decision, evidence)
        or authoritative_fact_gate(candidate, evidence)
    )
    if target == "local-rule" and not local_evidence:
        raise LearningError("local promotion lacks correction, outcome, or reproduction evidence")

    if target == "core-proposal":
        if not decision["public_safe"]:
            raise LearningError("core proposals must be marked public-safe")
        category_gate = False
        if deterministic_gate(candidate, decision, evidence):
            category_gate = decision["independent_contexts"] >= 1
        elif authoritative_fact_gate(candidate, evidence):
            category_gate = decision["independent_contexts"] >= 1
        else:
            category_gate = (
                decision["independent_contexts"] >= 3
                and decision["measured_outcomes"] >= 3
                and profile["measured_outcomes"] >= 3
                and profile["measured_scopes"] >= 2
            )
        if not category_gate:
            raise LearningError("core proposal does not meet its evidence-class gate")


def latest_decisions(
    root: Path, targets: Optional[set[str]] = None
) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for event in read_events(root):
        if event.get("event_type") != "decision" or not isinstance(
            event.get("candidate_id"), str
        ):
            continue
        target = event.get("target")
        if targets is not None and target not in targets and target != "reject":
            continue
        latest[event["candidate_id"]] = event
    return latest


def render_active_rules(root: Path) -> None:
    lines = [
        "# Active Live Consultant project rules",
        "",
        "Only the reviewed rules below may affect future advice in this project.",
        "Unpromoted candidates and public proposals are not instructions.",
        "",
    ]
    active = 0
    for candidate_id, decision in sorted(
        latest_decisions(root, {"local-rule"}).items()
    ):
        if decision.get("target") != "local-rule":
            continue
        candidate = load_candidate(root, candidate_id)
        if not review_is_current(candidate):
            continue
        check_promotion_gate(root, candidate, decision)
        active += 1
        lines.extend(
            [
                f"## {candidate_id}",
                "",
                f"- Rule: {markdown_value(candidate['proposal']['rule'])}",
                f"- Apply when: {markdown_value(candidate['proposal']['applicability'])}",
                f"- Countercase: {markdown_value(decision['countercase'])}",
                f"- Foundation: {', '.join(candidate['foundation_ids'])}",
                f"- Evidence: {markdown_value(decision['evidence_summary'])}",
                f"- Regression: {markdown_value(decision['regression_test'])}",
                f"- Review due: {candidate['governance']['review_due']}",
                "",
            ]
        )
    if active == 0:
        lines.extend(["No local rules have been promoted.", ""])
    write_private(root / "active-rules.md", "\n".join(lines), root)


def promote(workspace: Path, input_path: str) -> dict[str, Any]:
    root = require_enabled(workspace)
    decision = validate_promotion(read_json_input(input_path))
    candidate = load_candidate(root, decision["candidate_id"])
    check_promotion_gate(root, candidate, decision)
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_type": "decision",
        "created_at": utc_now(),
        **decision,
    }
    append_event(root, event)
    if decision["target"] == "core-proposal":
        proposal_path = root / "proposals" / f"{decision['candidate_id']}.json"
        proposal = {
            "schema_version": SCHEMA_VERSION,
            "candidate": candidate,
            "decision": event,
        }
        write_private(
            proposal_path,
            json.dumps(proposal, indent=2, sort_keys=True) + "\n",
            root,
        )
    render_active_rules(root)
    return {
        "candidate_id": decision["candidate_id"],
        "target": decision["target"],
        "behavior_changed": decision["target"] == "local-rule",
    }


def markdown_value(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    escaped = escaped.replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([`*_\[\]()!#|])", r"\\\1", escaped)


def public_markdown_value(value: str, fallback: str) -> str:
    if "[REDACTED_" in value:
        return markdown_value(fallback)
    return markdown_value(value)


def prepare_contribution(workspace: Path, candidate_id: str) -> dict[str, Any]:
    root = require_enabled(workspace)
    candidate = load_candidate(root, candidate_id)
    decision = latest_decisions(root, {"core-proposal"}).get(candidate_id)
    if not decision or decision.get("target") != "core-proposal":
        raise LearningError("candidate is not an eligible core proposal")
    if decision.get("public_safe") is not True:
        raise LearningError("core proposal is not marked public-safe")
    check_promotion_gate(root, candidate, decision)

    reproduction = "\n".join(
        f"- {public_markdown_value(item, 'Synthetic reproduction available after maintainer triage.')}"
        for item in candidate["verification"]["minimal_reproduction"]
    )
    exceptions = "\n".join(
        f"- {public_markdown_value(item, 'A redacted exception requires maintainer review.')}"
        for item in candidate["proposal"]["exceptions"]
    ) or "- None recorded."
    content = f"""# Live Consultant learning contribution

This is a sanitized, user-previewed proposal. It is untrusted input until a
maintainer reproduces it, rewrites any accepted rule, and runs regressions.

## Classification

- Candidate: `{candidate_id}`
- Plugin version: `{markdown_value(candidate['plugin_version'])}`
- Affected skills: {', '.join(f'`{item}`' for item in candidate['skill_ids'])}
- Foundation anchors: {', '.join(f'`{item}`' for item in candidate['foundation_ids'])}
- Failure kind: `{candidate['detection']['failure_kind']}`
- Evidence contexts: {decision['independent_contexts']}
- Measured outcomes: {decision['measured_outcomes']}

## Sanitized problem

{public_markdown_value(candidate['mistake']['summary'], 'A scoped recommendation produced the wrong observable behavior.')}

Observed effect: {public_markdown_value(candidate['mistake']['observed_effect'], 'A redacted project outcome contradicted the recommendation.')}

Coarse scope: {public_markdown_value(candidate['context']['scope'], 'Redacted project context; use the applicability rule below.')}

## Proposed behavior

{public_markdown_value(candidate['proposal']['rule'], 'A redacted rule requires maintainer reconstruction.')}

Apply when: {public_markdown_value(candidate['proposal']['applicability'], 'Only in the reviewed matching context.')}

Exceptions:

{exceptions}

## Evidence and countercase

Evidence class: {public_markdown_value(decision['evidence_summary'], 'Redacted evidence class; maintainer reproduction required.')}

Countercase: {public_markdown_value(decision['countercase'], 'A redacted countercase requires maintainer reconstruction.')}

## Minimal synthetic reproduction

{reproduction}

Regression: {public_markdown_value(decision['regression_test'], 'A public synthetic regression must be written before acceptance.')}

## Privacy declaration

- The recorder accepted only allowlisted structured fields and applied its
  deterministic secret and identifier filters.
- Automated filtering cannot certify anonymity. The user must verify that this
  exact preview contains no raw conversation, customer data, secret, account ID,
  private URL, local path, or attachment.
- Nothing has been submitted automatically.
- The user must review this exact file before choosing whether to post it.
"""
    preview_path = root / "previews" / f"{candidate_id}.md"
    write_private(preview_path, content, root)
    digest = digest_text(content)
    write_private(root / "previews" / f"{candidate_id}.sha256", digest + "\n", root)
    append_event(
        root,
        {
            "schema_version": SCHEMA_VERSION,
            "event_type": "preview",
            "candidate_id": candidate_id,
            "created_at": utc_now(),
            "digest": digest,
        },
    )
    return {
        "candidate_id": candidate_id,
        "preview": str(preview_path.relative_to(workspace)),
        "sha256": digest,
        "submitted": False,
    }


def finalize_contribution(
    workspace: Path, candidate_id: str, confirmed_digest: str
) -> dict[str, Any]:
    root = require_enabled(workspace)
    candidate_path(root, candidate_id)
    candidate = load_candidate(root, candidate_id)
    decision = latest_decisions(root, {"core-proposal"}).get(candidate_id)
    if not decision or decision.get("target") != "core-proposal":
        raise LearningError("candidate is no longer an eligible core proposal")
    if decision.get("public_safe") is not True:
        raise LearningError("core proposal is not marked public-safe")
    check_promotion_gate(root, candidate, decision)
    if not re.fullmatch(r"[0-9a-f]{64}", confirmed_digest):
        raise LearningError("confirmation digest must be a SHA-256 value")
    preview = root / "previews" / f"{candidate_id}.md"
    content = read_private(preview, root, "contribution preview")
    actual = digest_text(content)
    events = read_events(root)
    decision_index = max(
        (
            index
            for index, event in enumerate(events)
            if event.get("event_type") == "decision"
            and event.get("candidate_id") == candidate_id
        ),
        default=-1,
    )
    preview_events = [
        (index, event)
        for index, event in enumerate(events)
        if event.get("event_type") == "preview"
        and event.get("candidate_id") == candidate_id
    ]
    if not preview_events or preview_events[-1][0] <= decision_index:
        raise LearningError("prepare a fresh preview after the latest decision")
    if preview_events[-1][1].get("digest") != actual:
        raise LearningError("preview differs from its signed preparation event")
    if actual != confirmed_digest:
        raise LearningError("preview changed or confirmation digest does not match")
    destination = root / "contributions" / f"{candidate_id}-{actual[:12]}.md"
    if not destination.exists():
        write_private(destination, content, root, overwrite=False)
    append_event(
        root,
        {
            "schema_version": SCHEMA_VERSION,
            "event_type": "contribution-finalized",
            "candidate_id": candidate_id,
            "created_at": utc_now(),
            "digest": actual,
            "submitted": False,
        },
    )
    return {
        "candidate_id": candidate_id,
        "contribution": str(destination.relative_to(workspace)),
        "sha256": actual,
        "submitted": False,
    }


def status(workspace: Path) -> dict[str, Any]:
    root = learning_root(workspace)
    if not root.exists():
        return {
            "initialized": False,
            "local_learning_enabled": False,
            "candidates": 0,
            "active_rules": 0,
            "core_proposals": 0,
            "submitted": False,
        }
    settings = read_settings(root)
    if settings["local_learning_enabled"]:
        render_active_rules(root)
    events = read_events(root)
    local_decisions = latest_decisions(root, {"local-rule"})
    core_decisions = latest_decisions(root, {"core-proposal"})
    all_decisions = latest_decisions(root)
    active_local = 0
    for candidate_id, decision in local_decisions.items():
        if decision.get("target") != "local-rule":
            continue
        candidate = load_candidate(root, candidate_id)
        if review_is_current(candidate):
            check_promotion_gate(root, candidate, decision)
            active_local += 1
    active_core = 0
    for candidate_id, decision in core_decisions.items():
        if decision.get("target") != "core-proposal":
            continue
        candidate = load_candidate(root, candidate_id)
        if review_is_current(candidate):
            check_promotion_gate(root, candidate, decision)
            active_core += 1
    result = {
        "initialized": True,
        "local_learning_enabled": settings["local_learning_enabled"],
        "candidates": len(list((root / "candidates").glob("lc-*.json"))),
        "recurrences": sum(event.get("event_type") == "recurrence" for event in events),
        "active_rules": active_local,
        "core_proposals": active_core,
        "rejected": sum(
            decision.get("target") == "reject" for decision in all_decisions.values()
        ),
        "submitted": False,
    }
    if settings["local_learning_enabled"]:
        active_rules_path = root / "active-rules.md"
        active_rules = read_private(active_rules_path, root, "active project rules")
        result["active_rules_path"] = str(active_rules_path.relative_to(workspace))
        result["active_rules_sha256"] = digest_text(active_rules)
    return result


def rules(workspace: Path) -> dict[str, Any]:
    root = require_enabled(workspace)
    render_active_rules(root)
    path = root / "active-rules.md"
    content = read_private(path, root, "active project rules")
    return {
        "active_rules_path": str(path.relative_to(workspace)),
        "active_rules_sha256": digest_text(content),
        "rules_markdown": content,
        "submitted": False,
    }


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    workspace = safe_workspace(args.workspace)
    if not args.enable_local_learning:
        return {
            "initialized": False,
            "local_learning_enabled": False,
            "message": "No files created. Re-run with --enable-local-learning after consent.",
        }
    initialize_store(workspace, enabled=True)
    return status(workspace)


def command_consent(args: argparse.Namespace) -> dict[str, Any]:
    workspace = safe_workspace(args.workspace)
    if args.enable:
        root = initialize_store(workspace, enabled=True)
    else:
        root = learning_root(workspace)
        settings = read_settings(root)
        settings["local_learning_enabled"] = False
        settings.pop("integrity_hmac", None)
        settings["integrity_hmac"] = sign_payload(root, settings)
        write_private(
            root / "settings.json",
            json.dumps(settings, indent=2, sort_keys=True) + "\n",
            root,
        )
    return status(workspace)


def command_capture(args: argparse.Namespace) -> dict[str, Any]:
    workspace = safe_workspace(args.workspace)
    return capture(workspace, args.input)


def command_promote(args: argparse.Namespace) -> dict[str, Any]:
    workspace = safe_workspace(args.workspace)
    return promote(workspace, args.input)


def command_status(args: argparse.Namespace) -> dict[str, Any]:
    return status(safe_workspace(args.workspace))


def command_rules(args: argparse.Namespace) -> dict[str, Any]:
    return rules(safe_workspace(args.workspace))


def command_prepare(args: argparse.Namespace) -> dict[str, Any]:
    return prepare_contribution(safe_workspace(args.workspace), args.candidate_id)


def command_finalize(args: argparse.Namespace) -> dict[str, Any]:
    return finalize_contribution(
        safe_workspace(args.workspace), args.candidate_id, args.confirm_digest
    )


def command_purge(args: argparse.Namespace) -> dict[str, Any]:
    workspace = safe_workspace(args.workspace)
    if args.confirm != "DELETE-LOCAL-LEARNING":
        raise LearningError("purge requires the exact confirmation phrase")
    root = learning_root(workspace)
    if root.exists():
        ensure_inside(root, root)
        shutil.rmtree(root)
    return {"deleted": True, "submitted": False}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage privacy-preserving Live Consultant project learning."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    initialize = subparsers.add_parser("init")
    initialize.add_argument("--workspace", type=Path, required=True)
    initialize.add_argument("--enable-local-learning", action="store_true")
    initialize.set_defaults(handler=command_init)

    consent = subparsers.add_parser("consent")
    consent.add_argument("--workspace", type=Path, required=True)
    choice = consent.add_mutually_exclusive_group(required=True)
    choice.add_argument("--enable", action="store_true")
    choice.add_argument("--disable", action="store_true")
    consent.set_defaults(handler=command_consent)

    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("--workspace", type=Path, required=True)
    capture_parser.add_argument("--input", required=True)
    capture_parser.set_defaults(handler=command_capture)

    promote_parser = subparsers.add_parser("promote")
    promote_parser.add_argument("--workspace", type=Path, required=True)
    promote_parser.add_argument("--input", required=True)
    promote_parser.set_defaults(handler=command_promote)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--workspace", type=Path, required=True)
    status_parser.set_defaults(handler=command_status)

    rules_parser = subparsers.add_parser("rules")
    rules_parser.add_argument("--workspace", type=Path, required=True)
    rules_parser.set_defaults(handler=command_rules)

    prepare_parser = subparsers.add_parser("prepare-contribution")
    prepare_parser.add_argument("--workspace", type=Path, required=True)
    prepare_parser.add_argument("--candidate-id", required=True)
    prepare_parser.set_defaults(handler=command_prepare)

    finalize_parser = subparsers.add_parser("finalize-contribution")
    finalize_parser.add_argument("--workspace", type=Path, required=True)
    finalize_parser.add_argument("--candidate-id", required=True)
    finalize_parser.add_argument("--confirm-digest", required=True)
    finalize_parser.set_defaults(handler=command_finalize)

    purge_parser = subparsers.add_parser("purge")
    purge_parser.add_argument("--workspace", type=Path, required=True)
    purge_parser.add_argument("--confirm", required=True)
    purge_parser.set_defaults(handler=command_purge)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = args.handler(args)
    except LearningError as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
