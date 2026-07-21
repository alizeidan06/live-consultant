#!/usr/bin/env python3
"""Regression-test the long-form buyer-belief and visual-necessity contract."""

from __future__ import annotations

import json
import re
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL = PLUGIN_ROOT / "skills/design-offer-funnel/SKILL.md"
PROTOCOL = (
    PLUGIN_ROOT
    / "skills/design-offer-funnel/references/sales-letter-continuity.md"
)
COPY_QA = PLUGIN_ROOT / "skills/design-offer-funnel/references/copy-qa.md"


def split_sections(markdown: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", markdown))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections[match.group(1).strip()] = markdown[match.end() : end]
    return sections


def validate_contract(skill: str, protocol: str, copy_qa: str) -> list[str]:
    errors: list[str] = []
    sections = split_sections(protocol)

    if "references/sales-letter-continuity.md" not in skill:
        errors.append("design-offer-funnel does not load the continuity protocol")
    if "sales-letter-continuity.md" not in copy_qa:
        errors.append("copy QA does not route through the continuity protocol")

    required_sections = {
        "Governing distinction",
        "1. Build the belief spine before the page",
        "2. Write from square zero",
        "3. Create causal momentum",
        "4. Translate proof into business meaning",
        "5. Make visuals pay rent",
        "6. Earn the offer and action",
        "7. Run the deletion and skim passes",
        "Countercases and scope",
        "Regression prompts",
        "Definition of done",
    }
    for section in sorted(required_sections):
        body = sections.get(section)
        if body is None:
            errors.append(f"continuity protocol lost section: {section}")
        elif len(body.split()) < 12:
            errors.append(f"continuity protocol section is empty or too thin: {section}")

    required_contracts = {
        "framework_backstage": (
            "Governing distinction",
            "Keep research tables, awareness labels, funnel maps, the claim ledger",
        ),
        "material_terms_visible": (
            "Governing distinction",
            "the offer and its terms",
        ),
        "observable_actions": (
            "2. Write from square zero",
            "calls`, `messages`, `books`, `fills out the",
        ),
        "novice_paraphrase": (
            "2. Write from square zero",
            "novice paraphrase test",
        ),
        "causal_order": (
            "1. Build the belief spine before the page",
            "Give every paragraph and component one belief job",
        ),
        "deliberate_branches": (
            "1. Build the belief spine before the page",
            "Then branch deliberately",
        ),
        "proof_translation": (
            "4. Translate proof into business meaning",
            "raw change -> business result protected or created -> buyer meaning",
        ),
        "proof_proximity": (
            "4. Translate proof into business meaning",
            "moment the reader would naturally doubt",
        ),
        "visual_necessity": (
            "5. Make visuals pay rent",
            "visual necessity test",
        ),
        "copy_synced_motion": (
            "5. Make visuals pay rent",
            "Copy-synced motion should change the evidence",
        ),
        "ready_buyer_exit": (
            "6. Earn the offer and action",
            "A clear above-the-fold offer and CTA may serve ready buyers",
        ),
        "earned_offer": (
            "6. Earn the offer and action",
            "Earn the intensified or restated offer",
        ),
        "headline_skim": (
            "7. Run the deletion and skim passes",
            "Headline-only test",
        ),
        "three_reader_red_team": (
            "7. Run the deletion and skim passes",
            "Three-reader test",
        ),
    }
    for contract, (section, phrase) in required_contracts.items():
        if phrase.casefold() not in sections.get(section, "").casefold():
            errors.append(f"copy continuity contract missing: {contract}")

    skill_contracts = {
        "skill_protocol_link": "references/sales-letter-continuity.md",
        "skill_branch_rule": "then branch deliberately and preserve continuity",
    }
    for contract, phrase in skill_contracts.items():
        if phrase.casefold() not in skill.casefold():
            errors.append(f"design-offer-funnel contract missing: {contract}")

    qa_contracts = {
        "qa_ordered_spine": "ordered belief spine",
        "qa_observable_language": "observable nouns and verbs",
        "qa_proof_meaning": "business outcome kept, gained",
        "qa_visual_cost": "interpretation costs",
        "qa_ready_buyer_exit": "clear hero offer may serve ready buyers",
    }
    for contract, phrase in qa_contracts.items():
        if phrase.casefold() not in copy_qa.casefold():
            errors.append(f"copy QA contract missing: {contract}")

    countercases = {
        "ecommerce_visuals": "Ecommerce often needs product photography",
        "technical_diagram": (
            "Technical B2B buyers may understand an accurate architecture diagram"
        ),
        "warm_short_path": (
            "Warm, high-intent traffic may need a short purchase or booking path"
        ),
        "expert_language": "Expert audiences may prefer precise domain language",
        "high_stakes_tone": (
            "Regulated or high-stakes categories may require restrained humor"
        ),
    }
    countercase_text = sections.get("Countercases and scope", "")
    for countercase, phrase in countercases.items():
        if phrase.casefold() not in countercase_text.casefold():
            errors.append(f"copy continuity countercase missing: {countercase}")

    regression_labels = (
        "Novice service owner",
        "Warm ecommerce buyer",
        "Technical B2B committee",
        "Education with a ready-buyer exit",
        "High-stakes professional service",
    )
    regression_text = sections.get("Regression prompts", "")
    for label in regression_labels:
        if label.casefold() not in regression_text.casefold():
            errors.append(f"copy continuity regression prompt missing: {label}")

    contradiction_patterns = {
        "force_framework_surface": (
            r"\b(?:always|must)\s+(?:expose|show|display)\b.{0,120}"
            r"\b(?:awareness|framework|journey)"
        ),
        "repeat_same_cta_everywhere": (
            r"\brepeat\b.{0,60}\bcta\b.{0,60}\b(?:every|each)\b"
        ),
        "prefer_decorative_motion": r"\bprefer\s+decorative\s+motion\b",
    }
    all_contract_text = "\n".join((skill, protocol, copy_qa))
    for contradiction, pattern in contradiction_patterns.items():
        if re.search(pattern, all_contract_text, flags=re.IGNORECASE | re.DOTALL):
            errors.append(f"copy continuity contradiction present: {contradiction}")

    return errors


def main() -> int:
    try:
        skill = SKILL.read_text(encoding="utf-8")
        protocol = PROTOCOL.read_text(encoding="utf-8")
        copy_qa = COPY_QA.read_text(encoding="utf-8")
    except OSError as exc:
        print(
            json.dumps(
                {"errors": [f"copy continuity files unavailable: {exc}"]},
                indent=2,
            )
        )
        return 1

    errors = validate_contract(skill, protocol, copy_qa)
    mutation_cases = {
        "remove_framework_backstage": (
            skill,
            protocol.replace(
                "Keep research tables, awareness labels, funnel maps, the claim ledger",
                "",
                1,
            ),
            copy_qa,
        ),
        "force_framework_surface": (
            skill,
            protocol
            + "\nAlways expose awareness stages as numbered customer-facing diagrams.\n",
            copy_qa,
        ),
        "repeat_same_cta_everywhere": (
            skill,
            protocol + "\nRepeat the same CTA in every section.\n",
            copy_qa,
        ),
        "prefer_decorative_motion": (
            skill,
            protocol + "\nPrefer decorative motion even when it adds no proof.\n",
            copy_qa,
        ),
        "remove_ready_buyer_countercase": (
            skill,
            protocol.replace("Education with a ready-buyer exit", "", 1),
            copy_qa,
        ),
    }
    mutation_errors: list[str] = []
    for mutation, (mutated_skill, mutated_protocol, mutated_copy_qa) in (
        mutation_cases.items()
    ):
        if not validate_contract(mutated_skill, mutated_protocol, mutated_copy_qa):
            mutation_errors.append(
                f"copy continuity validator accepted destructive mutation: {mutation}"
            )
    errors.extend(mutation_errors)

    summary = {
        "contract_checks": 26,
        "countercases": 5,
        "errors": errors,
        "manual_model_review_prompts": 5,
        "mutation_guards": len(mutation_cases),
        "sections": 11,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
