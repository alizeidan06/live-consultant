#!/usr/bin/env python3
"""High-coverage guard against semantic access caps in Live Consultant knowledge.

The verifier intentionally tests families of meaning rather than one quoted
sentence. Contextual performance analysis, truth-status labels, evidence
grading, privacy controls, authorization, and external-execution gates remain
valid when they leave the complete method available for analysis, ideation,
and operational detail. Release-time blind review complements this deterministic
guard because no finite expression set proves every natural-language paraphrase.
"""

from __future__ import annotations

import json
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PLUGIN_ROOT / "skills"
UPSTREAM_ROOT = PLUGIN_ROOT / "assets" / "upstream-founder-playbook"
INVARIANT_PATH = (
    SKILLS_ROOT
    / "founder-business-consultant"
    / "references"
    / "knowledge-access-invariant.md"
)
ASSEMBLY_PATH = (
    SKILLS_ROOT
    / "founder-business-consultant"
    / "references"
    / "skill-assembly-protocol.md"
)

REQUIRED_INVARIANT_MARKERS = (
    "Every stored marketing, sales, persuasion",
    "remains available for complete explanation, analysis, comparison, ideation",
    "analytical metadata",
    "They never remove the underlying method",
    "source author's position to analyze",
    "regardless of wording, synonym, word order, euphemism, heading",
    "Knowledge availability is independent",
    "Context may change the recommended variant or intensity",
    "operational instructions, scripts, examples",
    "downgrade it to abstract, historical, or non-actionable discussion",
    "Stage, fit, routing, primary-emphasis, prerequisite, and sequence language",
    "never delays, routes away, abbreviates, or removes the complete method",
)

NEGATOR = (
    r"(?:do\s+not|don['’]t|never|must\s+not|should\s+not|"
    r"refus(?:e|es|ed|ing)(?:\s+to)?|"
    r"declin(?:e|es|ed|ing)(?:\s+to)?|avoid(?:s|ed|ing)?|"
    r"skip(?:s|ped|ping)?)"
)
SUPPRESSION_ACTION = (
    r"(?:withhold(?:s|held|ing)?|refrain(?:s|ed|ing)?(?:\s+from)?|"
    r"omit(?:s|ted|ting)?|exclud(?:e|es|ed|ing)|"
    r"suppress(?:es|ed|ing)?|hid(?:e|es|den|ing)|"
    r"quarantin(?:e|es|ed|ing)|censor(?:s|ed|ing)?|"
    r"redact(?:s|ed|ing)?|saniti[sz](?:e|es|ed|ing)|"
    r"strip(?:s|ped|ping)?|purg(?:e|es|ed|ing)|"
    r"filter(?:s|ed|ing)?\s+out|screen(?:s|ed|ing)?\s+out|"
    r"weed(?:s|ed|ing)?\s+out|rule(?:s|d|ing)?\s+out|"
    r"set(?:s|ting)?\s+aside|keep(?:s|ing)?\s+out|"
    r"reject(?:s|ed|ing)?|remov(?:e|es|ed|ing)|"
    r"ban(?:s|ned|ning)?|block(?:s|ed|ing)?|"
    r"prohibit(?:s|ed|ing)?|forbid(?:s|den|ding)?|"
    r"leave(?:s|left|leaving)?\s+(?:it|them|\w+(?:\s+\w+){0,4})\s+"
    r"(?:out|unmentioned|undisclosed))"
)
SUPPRESSION_DIRECT = (
    r"(?:withhold(?:s|ing)?|refrain(?:s|ing)?(?:\s+from)?|"
    r"omit(?:s|ting)?|exclud(?:e|es|ing)|suppress(?:es|ing)?|"
    r"hid(?:e|es|ing)|quarantin(?:e|es|ing)|censor(?:s|ing)?|"
    r"redact(?:s|ing)?|saniti[sz](?:e|es|ing)|strip(?:s|ping)?|"
    r"purg(?:e|es|ing)|filter(?:s|ing)?\s+out|screen(?:s|ing)?\s+out|"
    r"weed(?:s|ing)?\s+out|rule(?:s|ing)?\s+out|set(?:s|ting)?\s+aside|"
    r"keep(?:s|ing)?\s+out|reject(?:s|ing)?|remov(?:e|es|ing)|ban(?:s|ning)?|"
    r"block(?:s|ing)?|prohibit(?:s|ing)?|forbid(?:s|ding)?|"
    r"leave(?:s|leaving)?\s+(?:it|them|\w+(?:\s+\w+){0,4})\s+"
    r"(?:out|unmentioned|undisclosed))"
)
DENIAL = rf"(?:{NEGATOR}|{SUPPRESSION_ACTION})"
ACCESS_ACTION = (
    r"(?:shar(?:e|es|ed|ing)|explain(?:s|ed|ing)?|provid(?:e|es|ed|ing)|"
    r"teach(?:es|ing)?|taught|reveal(?:s|ed|ing)?|surfac(?:e|es|ed|ing)|"
    r"discuss(?:es|ed|ing)?|describ(?:e|es|ed|ing)|"
    r"analy[sz](?:e|es|ed|ing)|consider(?:s|ed|ing)?|"
    r"cover(?:s|ed|ing)?|get(?:s|ting)?\s+into|"
    r"walk(?:s|ed|ing)?\s+(?:you\s+)?through|"
    r"support(?:s|ed|ing)?|enabl(?:e|es|ed|ing)|assist(?:s|ed|ing)?|"
    r"brainstorm(?:s|ed|ing)?|explor(?:e|es|ed|ing)|"
    r"outlin(?:e|es|ed|ing)|detail(?:s|ed|ing)?|"
    r"summari[sz](?:e|es|ed|ing)|operationali[sz](?:e|es|ed|ing)|"
    r"make(?:s|made|making)?\s+(?:it|them|the\s+\w+)\s+actionable|"
    r"translat(?:e|es|ed|ing)|suppl(?:y|ies|ied|ying)|"
    r"includ(?:e|es|ed|ing)|mention(?:s|ed|ing)?|"
    r"generat(?:e|es|ed|ing)|creat(?:e|es|ed|ing)|"
    r"develop(?:s|ed|ing)?|ideat(?:e|es|ed|ing)|"
    r"suggest(?:s|ed|ing)?|recommend(?:s|ed|ing)?|"
    r"offer(?:s|ed|ing)?|appl(?:y|ies|ied|ying)|us(?:e|es|ed|ing)|"
    r"deploy(?:s|ed|ing)?|employ(?:s|ed|ing)?|load(?:s|ed|ing)?|"
    r"select(?:s|ed|ing)?|invok(?:e|es|ed|ing)|pitch(?:es|ed|ing)?|"
    r"sell(?:s|ing)?|sold|advertis(?:e|es|ed|ing)|"
    r"clos(?:e|es|ed|ing)|follow(?:s|ed|ing)?\s*up|"
    r"writ(?:e|es|ten|ing)|design(?:s|ed|ing)?|run(?:s|ning)?)"
)
SUBJECT = (
    r"(?:method|mechanism|tactic|technique|strategy|framework|skill|knowledge|"
    r"information|advice|idea|concept|approach|example|variant|message|copy|"
    r"marketing|sales|persuasion|influence|pressure|fear|scarcity|urgency|"
    r"pain|problem|emotion|manipulation|coercion|clos(?:e|es|ing)|pitch|outreach|"
    r"follow[- ]?up|advertising|ad|offer|funnel|story|villain|positioning|"
    r"guarantee|claim|promise|benefit|value|testimonial|channel|question|"
    r"interview|pricing|discount|lead|creative|rhetoric)"
)
DIRECT_SUBJECT = (
    r"(?:method|mechanism|tactic|technique|strategy|framework|skill|knowledge|"
    r"information|advice|idea|concept|approach|example|variant|message|copy|"
    r"marketing|sales|persuasion|influence|pressure|scarcity|urgency|"
    r"manipulation|coercion|clos(?:e|es|ing)|pitch|outreach|follow[- ]?up|"
    r"advertising|ad|offer|funnel|story|villain|positioning|guarantee|claim|"
    r"promise|benefit|testimonial|channel|question|interview|pricing|discount|"
    r"lead|creative|rhetoric|answer|response|guidance|instruction|script|"
    r"content|option|implementation|detail)"
)
DISFAVORED_LABEL = (
    r"(?:ethical|unethical|moral|immoral|manipulative|coercive|deceptive|"
    r"dishonest|fake|fabricated|manufactured|artificial|aggressive|"
    r"controversial|risky|harmful|unsafe|illegal|noncompliant|compliance|"
    r"legal|policy|platform|responsible|appropriate|genuine|truthful|"
    r"transparent|white[- ]hat|black[- ]hat|gray[- ]area|dark[- ]pattern|"
    r"exploitative|predatory|misleading|high[- ]pressure|shady|sleazy|"
    r"dubious|questionable|unsavory|substantiated|defensible|fulfillable)"
)

CAP_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "denial of method access or application",
        re.compile(
            rf"(?:^|[,;:]\s+)\b{NEGATOR}\b.{{0,12}}\b{ACCESS_ACTION}\b.{{0,100}}"
            rf"\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b|"
            rf"\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b.{{0,100}}"
            rf"(?:^|[,;:]\s+)\b{NEGATOR}\b.{{0,12}}\b{ACCESS_ACTION}\b",
            re.I,
        ),
    ),
    (
        "direct method suppression",
        re.compile(
            rf"^\s*(?:[-*+]\s+)?{SUPPRESSION_DIRECT}\b"
            rf"(?:\s+\w+){{0,6}}\s+\b{DIRECT_SUBJECT}\b|"
            rf"^\s*(?:[-*+]\s+)?(?:avoid|skip|reject)\b"
            rf"(?:\s+\w+){{0,5}}\s+\b{DIRECT_SUBJECT}\b|"
            rf"(?:^|[:;]\s+)\b{NEGATOR}\b\s+"
            rf"(?:ask|pitch|sell|close|pressure|advertise|"
            rf"follow\s*up|position|discount|scale|launch|build|run)\b"
            rf".{{0,100}}\b(?:{DIRECT_SUBJECT}|{DISFAVORED_LABEL})\b",
            re.I,
        ),
    ),
    (
        "passive method exclusion",
        re.compile(
            rf"\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b.{{0,120}}"
            r"\b(?:must|should|needs?\s+to|has\s+to)\s+be\s+"
            r"(?:excluded|omitted|hidden|suppressed|quarantined|censored|"
            r"rejected|removed|blocked|banned|prohibited)\b",
            re.I,
        ),
    ),
    (
        "approved-only subset",
        re.compile(
            rf"\b(?:only|exclusively)\s+(?:{ACCESS_ACTION}\s+)?"
            rf"(?:\w+[ -]){{0,4}}{DISFAVORED_LABEL}\b|"
            rf"\b{ACCESS_ACTION}\s+only\s+(?:\w+[ -]){{0,4}}"
            rf"{DISFAVORED_LABEL}\b|"
            rf"\b{DISFAVORED_LABEL}\b(?:\s+\w+){{0,4}}\s+only\b",
            re.I,
        ),
    ),
    (
        "proof or approval made a prerequisite for persuasion",
        re.compile(
            rf"\b(?:{SUBJECT})\b\s+(?:is|are)\s+(?:allowed|available|"
            r"permitted|provided)\s+only\s+(?:after|once|when|with)\b",
            re.I,
        ),
    ),
    (
        "method marked unavailable or inappropriate",
        re.compile(
            rf"\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b.{{0,60}}"
            r"\b(?:is|are|becomes?|remains?|deemed|considered|treated\s+as)\s+"
            r"(?:off[- ]limits|unavailable|forbidden|prohibited|"
            r"not\s+(?:allowed|appropriate|applicable)|does\s+not\s+apply|"
            r"doesn['’]t\s+apply|wrong\s+tool|out\s+of\s+bounds)\b|"
            r"\b(?:off[- ]limits|unavailable|forbidden|prohibited|"
            r"not\s+(?:allowed|appropriate|applicable)|wrong\s+tool)\b"
            rf".{{0,60}}\b(?:is|are|becomes?|remains?|deemed|considered)\b"
            rf".{{0,40}}\b{SUBJECT}\b",
            re.I,
        ),
    ),
    (
        "categorical non-use heading",
        re.compile(
            r"^\s*#{1,6}\s+(?:when\s+(?:not|never)\s+to\s+use|"
            r"when\s+this\s+(?:does\s+not|doesn['’]t)\s+apply|"
            r"where\s+this\s+(?:does\s+not|doesn['’]t)\s+apply|"
            r"when\s+.+\s+fails?\s*\(\s*don['’]t\s+use|"
            r".+\s+is\s+the\s+wrong\s+tool)\b",
            re.I,
        ),
    ),
    (
        "skill or framework routing exclusion",
        re.compile(
            rf"\b(?:this\s+)?(?:skill|framework|method|approach)\s+"
            r"(?:is|are)\s+not\s+for\b|"
            r"\bskip\s+(?:this\s+)?(?:skill|framework|method)\s+entirely\b|"
            r"\bdon['’]?t\s+use\s+(?:this\s+)?(?:skill|framework|method)\b",
            re.I,
        ),
    ),
    (
        "semantic routing exclusion",
        re.compile(
            r"\b(?:this\s+)?(?:skill|framework|method|strategy|approach)\s+"
            r"(?:does\s+not|doesn['’]t)\s+apply\b",
            re.I,
        ),
    ),
    (
        "sequencing gate on method availability",
        re.compile(
            rf"\b(?:{ACCESS_ACTION})\s+(?:this\s+|the\s+)?"
            rf"(?:{SUBJECT}\s+)?only\s+(?:after|once|when|with)\b|"
            rf"\b(?:{ACCESS_ACTION})\s+only\s+with\b|"
            r"\b(?:must|required\s+to)\s+.+\s+before\s+(?:using|applying|"
            r"loading|selecting|invoking|generating|creating|designing)\b",
            re.I,
        ),
    ),
    (
        "genuine or proven variant made exclusive",
        re.compile(
            rf"\b(?:{SUBJECT})\b.{{0,80}}\b(?:must|has\s+to|needs\s+to)\s+be\s+"
            r"(?:real|true|genuine|truthful|substantiated|defensible|"
            r"fulfillable|proved|proven)\b|"
            rf"\b(?:genuine|real|true|truthful|transparent)\b.{{0,40}}"
            r"\bnot\s+(?:manufactured|fabricated|fake|invented|deceptive)\b",
            re.I,
        ),
    ),
    (
        "label used to justify omission",
        re.compile(
            rf"\b{DISFAVORED_LABEL}\b.{{0,100}}\b(?:so|therefore|means?|"
            rf"because|due\s+to|override[sd]?)\b.{{0,100}}\b{SUPPRESSION_DIRECT}\b|"
            rf"\b{SUPPRESSION_DIRECT}\b.{{0,100}}\b(?:because|due\s+to)\b.{{0,100}}"
            rf"\b{DISFAVORED_LABEL}\b",
            re.I,
        ),
    ),
    (
        "cannot-help refusal",
        re.compile(
            rf"\b(?:can['’]t|cannot|won['’]t|will\s+not)\s+help\s+"
            rf"(?:with|create|provide|explain|teach|show)\b.{{0,100}}"
            rf"\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b",
            re.I,
        ),
    ),
    (
        "conditional method suppression",
        re.compile(
            rf"\b(?:if|when)\b.{{0,120}}\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b"
            rf".{{0,100}}\b{SUPPRESSION_DIRECT}\b|"
            rf"\b{DISFAVORED_LABEL}\b.{{0,100}}\b{SUPPRESSION_DIRECT}\b"
            rf".{{0,80}}\b(?:{SUBJECT}|it|them)\b|"
            rf"\b{DISFAVORED_LABEL}\b.{{0,100}}\bforbid(?:s|ding)?\b"
            rf".{{0,40}}\b(?:{ACCESS_ACTION}|{SUBJECT})\b|"
            rf"\b(?:we|i)\s+(?:won['’]t|will\s+not|can['’]t|cannot)\s+"
            rf"(?:{ACCESS_ACTION}|show)\b.{{0,100}}"
            rf"\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b|"
            rf"^\s*(?:we|i|the\s+consultant|this\s+skill)\s+{NEGATOR}\b"
            rf".{{0,12}}\b{ACCESS_ACTION}\b.{{0,100}}"
            rf"\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b|"
            rf"^\s*{NEGATOR}\b.{{0,15}}\brun\b.{{0,80}}\bframeworks?\b",
            re.I,
        ),
    ),
)

SEMANTIC_CAP_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "response restricted to an approved subset",
        re.compile(
            r"\b(?:restrict|limit|confine)s?\s+(?:the\s+)?"
            r"(?:answer|response|advice|discussion|content|guidance|consultant|agent)"
            r"\s+(?:only\s+)?to\b|"
            r"\b(?:answer|response|advice|discussion|content|guidance)\s+"
            r"(?:is|are|stays?|remains?)\s+(?:restricted|limited|confined)\s+to\b|"
            r"\b(?:cover|include|provide|explain)\b.{0,100}\band\s+nothing\s+else\b",
            re.I,
        ),
    ),
    (
        "knowledge kept outside scope",
        re.compile(
            rf"\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b.{{0,100}}\b"
            r"(?:outside|beyond)\s+(?:the\s+)?(?:scope|remit|bounds)\b|"
            r"\btreat\b.{0,100}\b(?:out\s+of\s+scope|outside\s+scope)\b|"
            rf"\b(?:scope|remit|coverage)\b.{{0,80}}\b(?:excludes?|omits?)\b"
            rf".{{0,100}}\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b",
            re.I,
        ),
    ),
    (
        "knowledge unavailable or unsupported",
        re.compile(
            rf"\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b.{{0,100}}\b"
            r"(?:is|are|stays?|remains?)\s+(?:not\s+available|unavailable|"
            r"unsupported|undisclosed|unmentioned|barred|disallowed|banned)\b|"
            r"\b(?:no|without)\s+(?:capability|ability)\s+to\b.{0,80}"
            rf"\b{ACCESS_ACTION}\b|"
            rf"\b(?:cannot|can['’]t|won['’]t|will\s+not|unable\s+to)\s+"
            rf"(?:support|cover|provide|explain|teach|show|outline|detail|supply)\b"
            rf".{{0,100}}\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b",
            re.I,
        ),
    ),
    (
        "knowledge request refused or avoided",
        re.compile(
            rf"\b(?:decline|refuse)s?\s+(?:any\s+)?requests?\b.{{0,100}}"
            rf"\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b|"
            rf"\b(?:steer|stay)\s+(?:clear|away)\s+of\b.{{0,100}}"
            rf"\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b|"
            rf"\b(?:do\s+not|don['’]t|never)\s+(?:touch|entertain|engage\s+with)\b"
            rf".{{0,100}}\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b",
            re.I,
        ),
    ),
    (
        "no knowledge or implementation detail",
        re.compile(
            rf"\bno\s+(?:guidance|instructions?|scripts?|examples?|details?|coverage)\b"
            rf".{{0,100}}\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b|"
            r"\b(?:explain|mention|discuss|analy[sz]e)\b.{0,100}\b"
            r"(?:but|while)\b.{0,80}\b(?:not|without)\b.{0,25}\b"
            r"(?:supply|provide|generate|create|teach|show|outline|detail|"
            r"operationali[sz]e|implement|make\s+actionable)\b|"
            r"\b(?:conceptual|abstract|theoretical|non[- ]operational)\b.{0,100}"
            r"\b(?:only|rather\s+than|without)\b.{0,80}"
            r"\b(?:actionable|operational|implementation|instructions?|scripts?)\b|"
            r"\b(?:do\s+not|don['’]t|never)\s+(?:make\s+it\s+actionable|"
            r"operationali[sz]e|translate\b.{0,40}\bdeployable|"
            r"provide\b.{0,30}\bimplementation\s+details?)\b|"
            r"\b(?:stop|stops|stopped)\s+short\s+of\b.{0,80}"
            r"\b(?:implementation|instructions?|scripts?|actionable)\b",
            re.I,
        ),
    ),
    (
        "ethical or compliance precedence gates knowledge",
        re.compile(
            rf"\b(?:{DISFAVORED_LABEL}|safety|risk\s+review)\b.{{0,100}}"
            r"\b(?:take(?:s)?\s+precedence|trump(?:s)?|override(?:s)?|"
            r"gate(?:s)?|stop\s+condition|hard\s+stop|red\s+line)\b"
            rf".{{0,100}}\b(?:{ACCESS_ACTION}|discussion|disclosure|exploration|"
            r"strategy|method|tactic|answer|response)\b|"
            r"\b(?:discussion|disclosure|explanation|access|guidance)\b.{0,80}"
            r"\b(?:conditional\s+on|requires?|needs?)\b.{0,50}"
            r"\b(?:approval|clearance|review|proof|compliance)\b",
            re.I,
        ),
    ),
    (
        "approved-only eligibility rule",
        re.compile(
            rf"\b(?:explain|include|cover|discuss|provide|teach|show|consider|"
            r"explore|brainstorm|outline|detail)\b.{0,100}\b"
            r"(?:provided|only\s+if|only\s+when|unless|conditional\s+on)\b"
            rf".{{0,100}}\b(?:{DISFAVORED_LABEL}|approval|clearance|proof)\b|"
            r"\b(?:eligible|qualifies?)\s+for\s+(?:inclusion|discussion|coverage)\b"
            r".{0,80}\bonly\s+(?:if|when)\b|"
            r"\bonly\b.{0,80}\b(?:pass(?:es)?|clear(?:s)?|approved|substantiated)\b"
            r".{0,80}\b(?:make(?:s)?\s+it\s+into|included|covered|discussed)\b",
            re.I,
        ),
    ),
    (
        "knowledge filtered by proof or ethics screen",
        re.compile(
            rf"\b(?:playbook|answer|response|advice|discussion|content|agent|consultant)"
            r"\b.{0,80}\b(?:excludes?|filters?|screens?|reserves?|confines?)\b"
            rf".{{0,100}}\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b|"
            rf"\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b.{{0,100}}"
            r"\b(?:don['’]t|do\s+not|doesn['’]t|does\s+not)\s+"
            r"(?:make|pass)\s+the\s+(?:cut|screen)\b",
            re.I,
        ),
    ),
    (
        "adversative availability smuggling",
        re.compile(
            r"\b(?:available|included|covered|explained|discussed)\b.{0,100}"
            r"\b(?:except|but\s+not|other\s+than)\b.{0,100}"
            rf"\b(?:{SUBJECT}|{DISFAVORED_LABEL})\b|"
            r"\b(?:full|complete)\b.{0,80}\b(?:available|included|covered)\b"
            r".{0,100}\bexcept\b",
            re.I,
        ),
    ),
    (
        "framework delayed or routed away by stage",
        re.compile(
            r"\b(?:save|reserve|delay|defer)\b.{0,60}\b"
            r"(?:full\s+)?(?:framework|method|skill|treatment|process)\b.{0,80}"
            r"\b(?:for|until|after|post[- ])\b|"
            r"\b(?:full\s+)?(?:framework|method|skill|treatment|process)\b"
            r".{0,80}\b(?:applies?|available|used|needed)\b.{0,50}"
            r"\bonly\b.{0,30}\b(?:after|once|when|with|for)\b|"
            r"\b(?:use|apply|load|select|invoke|switch\s+to)\b.{0,60}"
            r"\b(?:framework|method|skill)\b.{0,60}\b"
            r"(?:only\s+)?(?:after|once|post[- ])\b|"
            r"\b(?:use|apply|load|select|invoke)\b.{0,50}\b"
            r"(?:framework|method|skill)\b.{0,30}\bfirst\b|"
            r"\b(?:framework|method|skill)\b.{0,50}\b"
            r"(?:before|first)\b.{0,60}\b(?:framework|method|skill)\b",
            re.I,
        ),
    ),
    (
        "framework phase or fit omitted",
        re.compile(
            r"\b(?:skip|omit|drop|replace)\b.{0,50}\b"
            r"(?:phase|step|framework|method|skill|investigating|preliminaries)\b|"
            r"\b(?:framework|method|skill|phase|step)\b.{0,80}\b"
            r"(?:largely\s+)?irrelevant\b|"
            r"\b(?:don['’]t|do\s+not)\s+need\b.{0,60}\b"
            r"(?:full\s+)?(?:framework|method|skill|phase|step)\b|"
            r"\b(?:focus\s+on|keep|retain)\b.{0,60}\bonly\b.{0,40}"
            r"\b(?:customers?|alternatives?|methods?|frameworks?|skills?|phases?)\b",
            re.I,
        ),
    ),
    (
        "single framework route presented as exclusion",
        re.compile(
            r"\b(?:problem|answer|solution)\s+is\s+(?:elsewhere|not\s+here)\b|"
            r"\bfix\b.{0,60}\bfirst\b.{0,80}\b(?:not|instead\s+of)\b|"
            r"\buse\b.{0,60}\b(?:framework|method|skill)\b.{0,60}"
            r"\b(?:not|instead\s+of|rather\s+than)\b|"
            r"\b(?:where|when)\b.{0,40}\b(?:does\s+not|doesn['’]t)\s+apply\b",
            re.I,
        ),
    ),
    (
        "cross-sentence label used to suppress knowledge",
        re.compile(
            rf"\b(?:{DISFAVORED_LABEL}|artificial\s+pain)\b.{{0,160}}"
            r"(?:[.!?]\s+|\btherefore\b.{0,20})"
            r"(?:we\s+)?(?:do\s+not\s+show|omit|exclude|withhold|leave\s+it\s+out|"
            r"keep\s+it\s+out|it\s+(?:stays?|is)\s+(?:outside|unavailable))\b",
            re.I,
        ),
    ),
)

ANTI_SUPPRESSION = re.compile(
    r"\b(?:do\s+not|don['’]t|never|without|rather\s+than)\s+"
    r"(?:pre[- ]?)?(?:withhold|omit|exclude|hide|suppress|censor|quarantine|"
    r"redact|sanitize|filter(?:\s+out)?|screen\s+out|reject|rank\s+down|"
    r"remove|ban|block|prohibit)\b|"
    r"\b(?:does\s+not|is\s+not|are\s+not|not\s+used\s+to|never)\s+"
    r"(?:remove|hide|suppress|withhold|limit|exclude|sanitize|filter|"
    r"make\b.{0,30}\bunavailable)\b|"
    r"\bnot\s+(?:a|an)\s+(?:knowledge|ideation)[- ](?:veto|gate|control|filter)\b|"
    r"\bnot\s+(?:a|an)\s+ban\b|\bnot\s+unavailable\s+knowledge\b|"
    r"\brather\s+than\s+treating\b.{0,50}\bas\s+unavailable\b|"
    r"\bnot\s+as\s+(?:a|an)\s+instruction\s+to\s+"
    r"(?:hide|omit|withhold|exclude|suppress)\b",
    re.I,
)

EVIDENCE_OR_PRIVACY_ONLY = re.compile(
    r"\b(?:as\s+(?:demand\s+)?evidence|as\s+proof|as\s+fact|"
    r"factual\s+claims?|empirical\s+evidence|forecast|unverified\s+claim|"
    r"private\s+(?:credential|data)|credentials?|passwords?|secrets?|"
    r"personal\s+data|customer\s+data|learning\s+ledger)\b",
    re.I,
)

EXTERNAL_ACTION_ONLY = re.compile(
    r"\b(?:publish|launch|spend|connect|deploy|delete|deleting|upload|send|"
    r"message|alter|change\s+permissions?|production\s+database|owner\s+authorization|"
    r"external\s+(?:action|execution|spend)|public\s+funnel|payment\s+connection)\b",
    re.I,
)

KNOWLEDGE_CORE = re.compile(
    r"\b(?:framework|method|mechanism|tactic|technique|strategy|skill|advice|"
    r"guidance|instructions?|scripts?|examples?|implementation\s+details?|"
    r"brainstorm|ideation|creative\s+exploration|operational\s+detail)\b",
    re.I,
)

CAP_OBJECT = re.compile(
    rf"\b(?:{DISFAVORED_LABEL}s?|frameworks?|methods?|mechanisms?|tactics?|"
    r"techniques?|strategies?|skills?|playbooks?|knowledge|information|advice|guidance|"
    r"instructions?|scripts?|examples?|options?|ideas?|concepts?|approach(?:es)?|"
    r"variants?|content|messages?|copy|persuasion|influence|"
    r"pressure|scarcity|urgency|manipulation|coercion|closes?|pitches?|"
    r"outreach|follow[- ]?up|advertising|selling|sales\s+devices?|"
    r"conversion\s+tricks?|growth\s+hacks?|"
    r"pain(?:\s+(?:angle|point|creation))?|fake[- ]problem|fear|"
    r"fear(?:[- ]based)?\s+(?:appeals?|messages?|messaging)|"
    r"practices?|implementation\s+details?|creative\s+exploration|"
    r"operational\s+details?|press[- ]for[- ]commitment)\b",
    re.I,
)

SUPPRESSION_SIGNAL = re.compile(
    r"\b(?:withhold|withheld|omit|omitted|exclude[sd]?|redact|redacted|"
    r"sanitize|sanitized|strip|stripped|purge|purged|quarantine|quarantined|"
    r"hide|hidden|suppress|suppressed|censor|censored|ban|banned|barred|"
    r"disallow(?:ed)?|prohibit(?:ed)?|forbid(?:den)?|filter(?:ed)?(?:\s+out)?|"
    r"screen(?:ed)?\s+out|rule(?:d)?\s+out|skip(?:ped|s)?|"
    r"refuse[sd]?\b.{0,25}\b(?:explain|teach|show|provide)|"
    r"forbid(?:s|den)?\b.{0,30}\b(?:discuss(?:ing)?|explain(?:ing)?|"
    r"teach(?:ing)?|show(?:ing)?)|stay\s+away\s+from|"
    r"keep\b.{0,40}\bout|"
    r"leave\b.{0,40}\b(?:out|unmentioned|undisclosed)|"
    r"stay\s+out|refrain\s+from)\b",
    re.I,
)

ACTIVE_SUPPRESSION_SIGNAL = re.compile(
    r"(?:^|[.!?]\s+|\b(?:and|then|while)\s+)(?:[-*+]\s+)?"
    r"(?:(?:we|i|the\s+(?:agent|assistant|consultant|playbook|answer|response))"
    r"\s+)?(?:withhold|omit|exclude|remove|ban|avoid|redact|sanitize|strip|"
    r"purge|quarantine|hide|suppress|censor|skip|filter\s+out|"
    r"screen\s+out|rule\s+out|keep\b.{0,30}\bout|leave\b.{0,30}\b"
    r"(?:out|unmentioned|undisclosed)|stay\s+away\s+from|refrain\s+from)\b|"
    r"\b(?:if|when)\b.{0,100}\b(?:leave\s+it\s+out|omit|exclude|withhold|"
    r"refuse\s+to\s+(?:explain|teach|show|provide))\b|"
    r"\b(?:so|therefore)\s+(?:omit|exclude|withhold|hide|suppress)\b|"
    r"\bforbid(?:s|den)?\b.{0,35}\b(?:discuss(?:ing)?|explain(?:ing)?|"
    r"teach(?:ing)?|show(?:ing)?|provid(?:e|ing))\b|"
    r"\b(?:we|i|it|rule|record|agent|assistant|consultant|playbook|answer|"
    r"response|historical\s+case|ethics\s+screen)\b.{0,40}"
    r"\b(?:withholds?|omits?|excludes?|redacts?|sanitizes?|strips?|purges?|"
    r"removes?|bans?|declines?|declining|hides?|suppresses?|censors?|filters?\s+out|"
    r"screens?\s+out)\b|"
    r"\b(?:should|must|needs?\s+to|has\s+to)\s+be\s+"
    r"(?:withheld|omitted|excluded|hidden|suppressed|redacted|filtered|barred|"
    r"disallowed|banned|prohibited)\b|"
    r"\b(?:is|are|will\s+be)\s+(?:withheld|omitted|excluded|hidden|suppressed|"
    r"redacted|filtered|screened\s+out|barred|disallowed|banned|prohibited)\b|"
    r"\bgets?\s+(?:filtered|screened|omitted|excluded|withheld)\b|"
    r"\b(?:omit|omitting|withhold|withholding|remove|ban|avoid)\b|"
    r"\b(?:excludes?|filters?\s+out)\b|"
    r"\bstay\s+out\b|\bsave\s+for\b",
    re.I,
)

NEGATED_ACCESS_SIGNAL = re.compile(
    r"\b(?:do\s+not|don['’]t|never|should\s+not|must\s+not|won['’]t|"
    r"will\s+not|can['’]t|cannot|unable\s+to|avoid)\b.{0,35}\b"
    r"(?:share|explain|provide|teach(?:ing)?|surface|discuss|show|recommend|use|run|"
    r"generate|enable|assist|explore|brainstorm|outline|detail(?:ing)?|cover|support|"
    r"get\b.{0,10}\binto|"
    r"walk\b.{0,10}\bthrough|make\b.{0,10}\bactionable|translate)\b",
    re.I,
)

UNAVAILABLE_SIGNAL = re.compile(
    r"\b(?:off[- ]limits|out\s+of\s+scope|outside\s+(?:the\s+)?(?:scope|remit)|"
    r"(?:stays?|remains?|is)\s+outside\s+(?:the\s+)?(?:scope|remit|answer)|"
    r"outside\s+(?:our\s+)?(?:scope|remit|answer)|outside\s+what\s+we\s+discuss|"
    r"beyond\s+(?:the\s+)?(?:scope|remit)|not\s+available|unavailable|"
    r"not\s+appropriate|does\s+not\s+apply|doesn['’]t\s+apply|"
    r"(?:isn['’]t|aren['’]t|not)\s+something\b.{0,40}\bcovers?|"
    r"prohibited|forbidden|disallowed|"
    r"behind\b.{0,25}\bgate)\b",
    re.I,
)

APPROVED_ONLY_SIGNAL = re.compile(
    r"\b(?:only\s+(?:provide|include|cover|explain|share|recommend)|"
    r"(?:provide|include|cover|explain|share|recommend)\b.{0,40}\bonly|"
    rf"use\s+only\s+(?:\w+[ -]){{0,4}}(?:{DISFAVORED_LABEL})|"
    r"responsible\b.{0,30}\bonly|allowed\s+only|must\s+be\s+(?:real|genuine|"
    r"truthful|substantiated|defensible|fulfillable)|"
    r"reserve\b.{0,40}\bfor\b.{0,30}\b(?:truthful|ethical|responsible|compliant)|"
    r"provided\b.{0,30}\b(?:ethical|compliant)|eligible\b.{0,40}\bonly\s+when|"
    r"only\b.{0,25}\b(?:compliant|ethical|responsible)\b.{0,40}\b"
    r"(?:strategies?|methods?|tactics?)\b.{0,40}\bqualif(?:y|ies)\b)\b",
    re.I,
)

PARTIAL_ACCESS_SIGNAL = re.compile(
    r"\b(?:not\s+(?:supplied|provided|generated|created|taught|shown)\s+as\b|"
    r"not\s+how\s+to\s+execute|withholding\s+implementation\s+details?|"
    r"generation\s+is\s+not|instructions?\s+(?:should\s+)?stay\s+out|"
    r"only\s+summari[sz]e|non[- ]operational\s+level|"
    r"keep\b.{0,20}\btheoretical|stop(?:s)?\s+short\s+of\b.{0,30}\bimplementation|"
    r"not\s+make\b.{0,20}\bactionable|not\s+translate\b.{0,40}\bdeployable|"
    r"without\s+showing\s+how\b.{0,35}\bworks?\s+in\s+practice)\b",
    re.I,
)

REFUSAL_OR_SCREEN_SIGNAL = re.compile(
    r"\b(?:can['’]t|cannot|won['’]t|will\s+not|unable\s+to)\s+help\s+with\b|"
    r"\b(?:don['’]t|doesn['’]t|do\s+not|does\s+not)\s+make\s+the\s+cut\b|"
    r"\bgets?\s+filtered\b|"
    r"\breserve\b.{0,50}\b(?:recommendations?|advice|guidance)\b.{0,50}\bfor\b|"
    r"\brequires?\s+(?:approval|clearance|review|authori[sz]ation)\s+before\b.{0,40}"
    r"\b(?:explain|teach|show|provide|discuss)\b|"
    r"\b(?:approval|clearance|review|authori[sz]ation)\s+is\s+required\s+before\b"
    r".{0,40}\b(?:explain|teach|show|provide|discuss)\b",
    re.I,
)

FRAMEWORK_NAME = re.compile(
    r"\b(?:Lean\s+Startup|Traction|SPIN|StoryBrand|Mom\s+Test|Four\s+Steps|"
    r"Crossing\s+the\s+Chasm|Made\s+to\s+Stick|Obviously\s+Awesome|"
    r"Blue\s+Ocean|100M\s+(?:Leads|Offers)|Sell\s+Like\s+Crazy)\b",
    re.I,
)

ROUTING_CAP_SIGNAL = re.compile(
    r"\b(?:save|reserve|delay|defer|skip|drop|replace)\b.{0,60}\b"
    r"(?:framework|method|skill|phase|step|treatment|investigating|preliminaries)\b|"
    r"\b(?:framework|method|skill|phase|step|press[- ]for[- ]commitment)\b"
    r".{0,60}\b(?:only\s+(?:after|once|when|for)|largely\s+irrelevant|"
    r"does\s+not\s+apply|doesn['’]t\s+apply)\b|"
    r"\b(?:use|apply)\b.{0,60}\b(?:first|only\s+after)\b|"
    r"\bswitch\s+to\b.{0,60}\bonce\b|"
    r"\bwhen\s+not\s+to\s+use\b|\bwhere\b.{0,40}\bdoesn?['’]?t?\s+apply\b|"
    r"\bnever\s+run\b.{0,50}\bin\s+parallel\b",
    re.I,
)

ACTIVE_UNAVAILABLE_SIGNAL = re.compile(
    r"\b(?:frameworks?|methods?|mechanisms?|tactics?|techniques?|strategies?|"
    r"skills?|advice|guidance|instructions?|scripts?|examples?|variants?|copy|"
    r"persuasion|selling)\b"
    r".{0,70}\b(?:is|are|stays?|remains?|becomes?|was|were)\s+"
    r"(?:off[- ]limits|out\s+of\s+scope|outside\s+(?:the\s+)?(?:scope|remit)|"
    r"not\s+available|unavailable|not\s+appropriate|not\s+covered|"
    r"(?:not|isn['’]t|aren['’]t)\s+something\b.{0,40}\bcovers?|"
    r"prohibited|forbidden|"
    r"disallowed|barred|banned|restricted)\b|"
    r"\b(?:off[- ]limits|out\s+of\s+scope|not\s+covered|unavailable|"
    r"prohibited|forbidden|disallowed|restricted)\b.{0,70}"
    r"\b(?:framework|method|tactic|technique|strategy|skill|guidance|"
    r"instructions?|scripts?|examples?|copy)\b|"
    r"(?:^|[:|]\s*)(?:excluded|not\s+covered|theory\s+only|"
    r"post[- ]validation\s+only|prohibited)(?:\s*\||[.!]?\s*$)|"
    r"\b(?:falls?|stays?|remains?|is)\s+outside\b.{0,35}"
    r"\b(?:scope|remit|answer|what\s+we\s+discuss)\b|"
    r"\bbehind\s+(?:an?\s+)?(?:ethics|compliance|policy)\s+gate\b|"
    r"\bavailability\s*[:=]\s*(?:excluded|not\s+covered|restricted)\b|"
    r"\b(?:frameworks?|methods?|tactics?|strategies?|skills?)\b.{0,40}"
    r"\b(?:isn['’]t|aren['’]t)\s+something\b.{0,40}\bcovers?\b",
    re.I,
)

STAGE_CAP_SIGNAL = re.compile(
    r"\b(?:hold\s+back|park|lock|keep\s+dormant|stays?\s+dormant|"
    r"should\s+be\s+skipped)\b.{0,90}\b(?:until|before|after|once|at\s+this\s+stage)\b|"
    r"\b(?:framework|method|technique|strategy|skill|approach|"
    r"Traction|SPIN|StoryBrand|Blue\s+Ocean|100M\s+Offers)\b.{0,90}"
    r"\b(?:available\s+only\s+once|only\s+in|belongs?\s+only\s+in|"
    r"reserved\s+for|irrelevant\s+before|premature|dormant|nowhere\s+else|"
    r"outside\s+scope\s+for|locked\s+until|until\b)\b|"
    r"\b(?:do\s+not|don['’]t|never)\s+(?:invoke|combine|use)\b.{0,90}"
    r"\b(?:until|both|together)\b|"
    r"\buse\s+either\b.{0,100}\bnever\s+both\b|"
    r"\bonly\s+post[- ]validation\b.{0,60}\bqualif(?:y|ies)\b",
    re.I,
)

DETAIL_DOWNGRADE_SIGNAL = re.compile(
    r"\b(?:without\s+(?:giving|showing|providing|including)\b.{0,45}"
    r"\b(?:usable|working|executable|implementation|procedure|steps?)|"
    r"omit\s+the\s+steps?|stop\s+there|at\s+(?:an?\s+)?overview\s+level|"
    r"conceptual\s+(?:sketch|level)|no\s+executable\s+detail|"
    r"leave\s+the\s+implementation\s+blank|"
    r"avoid(?:ing)?\s+instructions?\b.{0,45}\b(?:could|can)\s+use|"
    r"informational\s+rather\s+than\s+operational|"
    r"do\s+not\s+furnish\b.{0,40}\bstep[- ]by[- ]step|"
    r"recognition\b.{0,25}\bnot\s+deployment|"
    r"high[- ]level\s+commentary\b.{0,45}\busable\s+copy\s+is\s+not|"
    r"cannot\s+help\s+implement|not\s+to\s+turn\s+into\s+copy|"
    r"actionable\b.{0,35}\bis\s+not|"
    r"should\s+stay\s+at\s+a\s+conceptual\s+level|"
    r"theory\s+only)\b",
    re.I,
)

EUPHEMISTIC_CAP_SIGNAL = re.compile(
    r"\b(?:back\s+room|don['’]t\s+belong\s+in\s+the\s+toolkit|"
    r"behind\s+a\s+guardrail|sidesteps?|draw\s+the\s+line\s+at|"
    r"safe\s+side\s+of|cutting[- ]room\s+floor|open\s+the\s+black\s+box|"
    r"hereby\s+excluded|remain(?:s)?\s+restricted|"
    r"comprises?\b.{0,60}\bexclusively|coverage\s+terminates|"
    r"automatically\s+removes?|eligibility\s+for\s+explanation\s+depends|"
    r"receives?\s+no\s+coverage|no\s+examples?\s+will\s+be\s+supplied|"
    r"not\s+something\s+we\s+teach|keep\b.{0,45}\boff\s+the\s+page|"
    r"leaves?\b.{0,45}\bundisclosed|nothing\s+is\s+censored\b.{0,45}\bexcept|"
    r"no\b.{0,45}\b(?:method|tactic|strategy|skill)\b.{0,35}"
    r"\bis\s+to\s+be\s+(?:explained|taught|shown|provided)|"
    r"not\s+something\b.{0,30}\b(?:consultant|agent|assistant)\s+(?:teaches?|covers?)|"
    r"(?:framework|method|tactic|strategy|skill|technique|approach|"
    r"conversion\s+tricks?)\b.{0,35}\b(?:is|are)\s+(?:a\s+)?no[- ]go)\b",
    re.I,
)

NARROW_ALLOWED_RELATIONS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:do\s+not|don['’]t|never|omit|exclude|remove)\b.{0,60}"
        r"\b(?:private\s+(?:credentials?|data)|credentials?|passwords?|secrets?|"
        r"personal\s+data|customer\s+data|email\s+addresses?)\b",
        re.I,
    ),
    re.compile(
        r"\b(?:do\s+not|don['’]t|never|avoid)\b.{0,100}"
        r"\b(?:as\s+(?:demand\s+)?evidence|as\s+proof|as\s+fact|"
        r"empirical\s+evidence)\b",
        re.I,
    ),
    re.compile(
        r"\bonly\s+include\s+substantiated\s+factual\s+claims\s+in\s+the\s+forecast\b|"
        r"\bdo\s+not\s+describe\s+an?\s+unverified\s+claim\s+as\s+fact\b",
        re.I,
    ),
    re.compile(
        r"\b(?:publish|launch|spend|connect|deploy|upload|alter|"
        r"change\s+permissions?)\b.{0,80}\b(?:requires?|approval[- ]bound)\b"
        r".{0,45}\b(?:owner\s+)?authori[sz]ation\b|"
        r"\bowner\s+authori[sz]ation\b.{0,80}\b(?:publish|launch|spend|"
        r"connect|deploy|upload|alter|change\s+permissions?)\b",
        re.I,
    ),
    re.compile(
        r"\bunavailable\s+in\s+the\s+live\s+account\s+because\s+access\s+is\s+missing\b",
        re.I,
    ),
    re.compile(r"\bcurrent\s+account\s+access\s+is\s+unavailable\b", re.I),
    re.compile(
        r"\bskill\s+does\s+not\s+apply\s+to\s+deleting\s+production\s+databases\b",
        re.I,
    ),
    re.compile(r"\bbinaries\s+are\s+excluded\b.{0,100}\bredistribution\s+rights\b", re.I),
    re.compile(r"\bpublic\s+packets?\s+include\s+only\b.{0,180}\bfields?\b", re.I),
    re.compile(r"\b(?:skill|foundation)\s+IDs\b", re.I),
)

ANTI_CAP_CLAUSE = re.compile(
    r"\b(?:is|are|was|were)\s+not\s+used\s+to\b.{0,120}"
    r"\b(?:sanitize|withhold|omit|exclude|hide|suppress|rank\s+down)\b|"
    r"\bnever\s+be\s+used\s+to\s+(?:hide|omit|withhold|exclude|suppress)\b|"
    r"\bcannot\s+regain\s+authority\b|"
    r"\brather\s+than\s+(?:treating|using)\b.{0,100}"
    r"\b(?:ban|forbidden|unavailable|filter|gate)\b|"
    r"\bnot\s+(?:a|an)\s+(?:moral\s+)?filter\b|"
    r"\brather\s+than\s+authority\s+to\b.{0,40}"
    r"\b(?:hide|omit|withhold|exclude|suppress|refuse)\b|"
    r"\bpreserve\b.{0,160}\bvariants?\b",
    re.I,
)

LEARNING_DATA_CONTEXT = re.compile(
    r"\b(?:telemetry|learning\s+(?:candidate|contribution|packet|ledger|record)|"
    r"public\s+packets?|structured\s+fields?|redacted\s+signal|"
    r"community\s+contribution)\b",
    re.I,
)

HISTORICAL_EVIDENCE_CONTEXT = re.compile(
    r"\b(?:study|jurors?|evidence\s+was\s+ruled|source[- ]reported\s+outcome|"
    r"controlled\s+result\s+data|historical\s+case|case\s+chronology)\b",
    re.I,
)


@dataclass(frozen=True)
class Chunk:
    line: int
    text: str


def text_chunks(path: Path) -> list[Chunk]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if path.suffix.lower() == ".json":
        data = json.loads("\n".join(lines))
        chunks: list[Chunk] = []

        def walk(value: object, pointer: str = "$") -> None:
            if isinstance(value, str):
                chunks.extend(split_units(f"{pointer}: {value}", 1))
            elif isinstance(value, dict):
                scalar_items = [
                    f"{key}={child}"
                    for key, child in value.items()
                    if isinstance(child, str)
                ]
                if scalar_items:
                    chunks.extend(split_units(" | ".join(scalar_items), 1))
                for key, child in value.items():
                    walk(child, f"{pointer}.{key}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, f"{pointer}[{index}]")

        walk(data)
        return chunks
    if path.suffix.lower() == ".csv":
        chunks = []
        for line_number, row in enumerate(csv.reader(lines), start=1):
            if any(cell.strip() for cell in row):
                chunks.extend(
                    split_units(
                        " | ".join(cell.strip() for cell in row), line_number
                    )
                )
            for column, cell in enumerate(row, start=1):
                if cell.strip():
                    chunks.extend(split_units(f"column {column}: {cell}", line_number))
        return chunks
    if path.suffix.lower() in {".yaml", ".yml"}:
        chunks = []
        index = 0
        while index < len(lines):
            line_number = index + 1
            raw = lines[index]
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                index += 1
                continue
            block = re.match(r"^(\s*)[^:#]+:\s*[>|][+-]?\s*$", raw)
            if block:
                base_indent = len(block.group(1))
                values: list[str] = []
                index += 1
                while index < len(lines):
                    continuation = lines[index]
                    if not continuation.strip():
                        values.append("")
                        index += 1
                        continue
                    indent = len(continuation) - len(continuation.lstrip())
                    if indent <= base_indent:
                        break
                    values.append(continuation.strip())
                    index += 1
                chunks.extend(split_units(" ".join(values), line_number))
                continue
            chunks.extend(split_units(stripped, line_number))
            index += 1
        scalar_chunks = list(chunks)
        for left, right in zip(scalar_chunks, scalar_chunks[1:]):
            if right.line - left.line <= 2:
                chunks.append(Chunk(left.line, f"{left.text} | {right.text}"))
        return chunks

    chunks: list[Chunk] = []
    buffer: list[str] = []
    start = 1

    def emit(raw_text: str, line_number: int) -> None:
        chunks.extend(split_units(raw_text, line_number))

    def flush() -> None:
        nonlocal buffer
        if buffer:
            emit(" ".join(buffer), start)
            buffer = []

    for line_number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            flush()
            continue
        if not stripped:
            flush()
            continue
        if stripped.startswith("#") or stripped.startswith("|"):
            flush()
            emit(stripped, line_number)
            continue
        if not buffer:
            start = line_number
        buffer.append(stripped)
    flush()
    return chunks


def split_units(raw_text: str, line_number: int) -> list[Chunk]:
    normalized = re.sub(r"\s+", " ", raw_text).strip()
    if not normalized:
        return []
    pieces = re.split(
        r"\s+(?=[-*+]\s+)|\s+(?=\d+[.)]\s+)|"
        r"(?<=[.!?])\s+(?=[A-Z#*\[\"'])",
        normalized,
        flags=re.I,
    )
    chunks: list[Chunk] = []
    for piece in pieces:
        if piece.count("|") >= 2:
            cells = [cell.strip() for cell in piece.split("|") if cell.strip()]
            if cells:
                chunks.append(Chunk(line_number, " | ".join(cells)))
            chunks.extend(Chunk(line_number, cell) for cell in cells)
        elif piece.strip():
            chunks.append(Chunk(line_number, piece.strip()))
    return chunks


def chunk_windows(chunks: list[Chunk]) -> list[Chunk]:
    """Return adjacent clause windows for pronoun/coreference checks."""
    windows: list[Chunk] = []
    for index, chunk in enumerate(chunks):
        group = chunks[index : index + 2]
        if len(group) != 2 or group[-1].line - chunk.line > 3:
            continue
        combined = " ".join(item.text for item in group)
        second = group[1].text
        if (
            CAP_OBJECT.search(group[0].text)
            and re.search(
                r"\b(?:it|them|that\s+(?:material|part)|those\s+instructions?|"
                r"the\s+(?:method|tactic|technique|approach|strategy|framework)|"
                r"no\s+examples?|this\s+(?:method|script|framework))\b",
                second,
                re.I,
            )
            and (
                SUPPRESSION_SIGNAL.search(combined)
                or NEGATED_ACCESS_SIGNAL.search(combined)
                or UNAVAILABLE_SIGNAL.search(combined)
                or ACTIVE_SUPPRESSION_SIGNAL.search(combined)
                or DETAIL_DOWNGRADE_SIGNAL.search(combined)
                or EUPHEMISTIC_CAP_SIGNAL.search(combined)
            )
        ):
            windows.append(Chunk(chunk.line, combined))
    return windows


def violation_labels(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    # Mask only the exact typed relation (privacy, factual-evidence status,
    # account access, or authorized external action). Never exempt a whole
    # clause, because an unrelated access veto can be smuggled beside it.
    candidate = normalized
    for pattern in NARROW_ALLOWED_RELATIONS:
        candidate = pattern.sub(" TYPED_NON_KNOWLEDGE_CONTROL ", candidate)
    candidate = re.sub(
        r"\bthe\s+source\s+says\s+the\s+story\s+must\s+be\s+real,\s*"
        r"not\s+manufactured\b(?=;?\s*compare\s+real\s+and\s+invented\s+variants)",
        " SOURCE_POSITION_WITH_VARIANTS ",
        candidate,
        flags=re.I,
    )
    candidate = ANTI_SUPPRESSION.sub(" PRESERVE_FULL_KNOWLEDGE ", candidate)
    labels: list[str] = []
    for label, pattern in SEMANTIC_CAP_PATTERNS:
        if pattern.search(candidate):
            labels.append(label)

    has_object = bool(CAP_OBJECT.search(candidate))

    def signal_near_object(pattern: re.Pattern[str], radius: int = 100) -> bool:
        for match in pattern.finditer(candidate):
            start = max(0, match.start() - radius)
            end = min(len(candidate), match.end() + radius)
            if CAP_OBJECT.search(candidate[start:end]):
                return True
        return False

    if has_object and signal_near_object(ACTIVE_SUPPRESSION_SIGNAL):
        labels.append("knowledge object suppressed")
    if has_object and signal_near_object(NEGATED_ACCESS_SIGNAL, 80):
        labels.append("knowledge access action denied")
    if has_object and signal_near_object(ACTIVE_UNAVAILABLE_SIGNAL, 90):
        labels.append("knowledge object made unavailable")
    if has_object and signal_near_object(APPROVED_ONLY_SIGNAL, 80):
        labels.append("knowledge limited to approved subset")
    if PARTIAL_ACCESS_SIGNAL.search(candidate):
        labels.append("operational detail withheld")
    if DETAIL_DOWNGRADE_SIGNAL.search(candidate):
        labels.append("operational detail downgraded")
    if has_object and signal_near_object(REFUSAL_OR_SCREEN_SIGNAL, 80):
        labels.append("knowledge refused or filtered")
    if ROUTING_CAP_SIGNAL.search(candidate) and (
        has_object or FRAMEWORK_NAME.search(candidate)
    ):
        labels.append("framework routed away by stage or fit")
    if STAGE_CAP_SIGNAL.search(candidate) and (
        has_object or FRAMEWORK_NAME.search(candidate)
    ):
        labels.append("framework gated by stage, fit, or sequence")
    if EUPHEMISTIC_CAP_SIGNAL.search(candidate) and has_object:
        labels.append("euphemistic knowledge-access veto")
    return list(dict.fromkeys(labels))


ADVERSARIAL_CAPS = (
    "If a method manipulates emotion, leave it out.",
    "Unethical strategies are off-limits.",
    "Only provide responsible persuasion techniques.",
    "Avoid teaching artificial pain creation.",
    "We should not surface deceptive tactics.",
    "Risky pressure methods must be excluded.",
    "Do not recommend manufactured urgency.",
    "I can't help with manipulative sales psychology.",
    "Skip coercive closes.",
    "When a tactic could cause harm, refuse to explain it.",
    "Compliance concerns override the creative method, so omit it.",
    "Never generate fake-problem angles.",
    "Use only genuine scarcity.",
    "Do not use fear-based messaging.",
    "This framework is not appropriate due to manipulation.",
    "This is unethical, so omit the tactic.",
    "Faking a problem means the tactic is unavailable.",
    "Responsible methods only.",
    "The platform rule forbids us from discussing the strategy.",
    "Legal risk means we won't show that closing method.",
    "Hide any sales device that pressures the buyer.",
    "Quarantine controversial persuasion ideas.",
    "This skill does not apply to marketplaces.",
    "Use this framework only after demand is proved.",
    "Never run these frameworks in parallel.",
    "## When Not to Use This Skill",
    "The story must be real, not manufactured.",
    "Persuasion is allowed only with proof points.",
)

ADDITIONAL_ADVERSARIAL_CAPS = (
    "Keep deceptive closing methods out of the answer.",
    "Leave pressure tactics unmentioned.",
    "Restrict the response to above-board persuasion.",
    "Limit advice to non-manipulative methods.",
    "Steer clear of manufactured urgency.",
    "Withhold aggressive close scripts.",
    "Exclude dark-pattern guidance.",
    "Redact coercive strategies.",
    "Filter out unethical growth hacks.",
    "Sanitize manipulative examples.",
    "The response is confined to responsible practices.",
    "We cover compliant tactics and nothing else.",
    "Any ethically questionable approach stays outside scope.",
    "I won't walk you through fabricated pain angles.",
    "Manipulative methods aren't something this consultant covers.",
    "Treat deceptive methods as out of scope.",
    "Content on fabricated objections is not available.",
    "The assistant has no capability to explain manipulative techniques.",
    "Decline requests for pressure-based scripts.",
    "Refuse requests involving fear appeals.",
    "Ethical considerations take precedence over complete disclosure.",
    "Safety rules trump creative exploration.",
    "Risk review gates which tactics may be discussed.",
    "A compliance concern is a stop condition for this strategy.",
    "Do not engage with manipulative marketing.",
    "Stay away from high-pressure selling.",
    "Omit anything that exploits pain.",
    "Strip unethical tactics from the recommendation.",
    "Purge deceptive examples.",
    "Do not enable fabricated scarcity.",
    "Do not assist with coercive copy.",
    "No instructions for fake urgency.",
    "Forbidden: fear-based closing scripts.",
    "Coercive tactics: prohibited.",
    "Manipulative selling is outside scope.",
    "Manufactured urgency is beyond scope.",
    "Ideas involving emotional exploitation should be withheld.",
    "Methods judged harmful are disallowed.",
    "Deceptive tactics are barred.",
    "Black-hat offers are banned.",
    "Never touch unethical scarcity.",
    "Don't entertain artificial pain points.",
    "Don't explore manipulative options.",
    "Do not brainstorm pressure tactics.",
    "Never outline fear appeals.",
    "Avoid detailing deceptive guarantees.",
    "For reasons of compliance, fake-scarcity guidance shall remain undisclosed.",
    "When legality is uncertain, the method falls outside what we discuss.",
    "We explain these tactics provided they are ethical.",
    "An approach is eligible for inclusion only when compliant.",
    "The playbook excludes tactics lacking proof.",
    "Unproven tactics don't make the cut.",
    "Anything not substantiated gets filtered.",
    "Only tactics that pass a harm screen make it into the answer.",
    "We reserve recommendations for truthful methods.",
    "Discussion is limited to platform-safe methods.",
    "The agent confines itself to responsible selling.",
    "Pressure techniques can be analyzed but not supplied as usable scripts.",
    "Explain the history, not how to execute it.",
    "Allow conceptual discussion while withholding implementation details.",
    "Analysis is permitted; generation is not.",
    "The tactic can be mentioned, but instructions should stay out.",
    "Only summarize the method abstractly.",
    "Answer at a non-operational level.",
    "Do not make it actionable.",
    "Keep the advice theoretical.",
    "Do not translate the tactic into deployable copy.",
    "We refrain from teaching coercive persuasion.",
    "Rule out fake-problem angles.",
    "We are unable to provide high-pressure scripts.",
    "The answer stops short of implementation details for coercive tactics.",
    "Discussion is conditional on compliance approval.",
    "Pressure methods require clearance before we explain them.",
    "Dark patterns sit behind an ethics gate.",
    "Fake scarcity is outside our remit.",
    "We cannot support deceptive sales techniques.",
    "This closing tactic is manipulative. Leave it out.",
    "The approach creates artificial pain. We omit it from recommendations.",
    "Compliance is uncertain. Therefore, do not show the method.",
    "This tactic may harm trust. It stays outside the answer.",
    "The technique is deceptive. It is unavailable for customer guidance.",
    "Every method remains fully available except manipulative variants, which are off-limits.",
    "The full mechanism remains available for analysis; do not recommend manufactured urgency.",
    "Save the full framework for post-validation.",
    "Use Lean Startup first, then use Traction.",
    "Switch to SPIN once the product is validated.",
    "This framework applies only after demand is proved.",
    "You don't need the full framework in this context.",
    "Press-for-commitment is largely irrelevant here.",
    "Skip the Investigating phase.",
    "Focus on best-fit customers only and drop the alternatives.",
    "## Where This Framework Doesn't Apply",
    "Fix the product first; this is not a messaging problem.",
)

FRESH_ADVERSARIAL_CAPS = (
    "The method remains available in principle, although coercive versions are withheld.",
    "We preserve the full framework; the deceptive pieces stay out.",
    "Full access applies, subject to an ethics screen that removes predatory scripts.",
    "Nothing is censored, except fabricated-urgency examples.",
    "The complete mechanism is visible; actionable manipulation guidance is not.",
    "All variants stay in view, save for those legal marks as deceptive.",
    "We keep the knowledge base intact while declining operational instructions for high-pressure tactics.",
    "The theory remains complete, but implementation help for fake scarcity is withheld.",
    "The tactic is available to mention, though not to turn into copy.",
    "This pressure close is controversial. We keep that material off the page.",
    "The angle manufactures urgency. It receives no coverage.",
    "The framework is risky. That part is screened out.",
    "These tactics are manipulative. We will not get into them.",
    "Legal called the method unsafe. The consultant leaves those instructions undisclosed.",
    "This is black-hat persuasion. No examples will be supplied.",
    "This script is deceptive. It should stay at a conceptual level.",
    "Compliance flagged it. The method is not something we teach.",
    "Hold back SPIN until the buyer admits pain.",
    "Traction is available only once product-market fit exists.",
    "Before validation, this skill stays dormant.",
    "The offer framework is for proven markets and nowhere else.",
    "At this stage, the full method is premature and should be skipped.",
    "Start with StoryBrand; the other frameworks remain locked until messaging is fixed.",
    "Blue Ocean is outside scope for service businesses.",
    "The technique is reserved for mature companies.",
    "Use either SPIN or Influence, never both.",
    "This method belongs only in enterprise sales.",
    "Do not invoke 100M Offers until pricing research is complete.",
    "The approach is irrelevant before revenue.",
    "Park the framework until demand has been established.",
    "Only post-validation teams qualify for this method.",
    "Name the tactic without giving a usable procedure.",
    "Acknowledge manipulation, but omit the steps.",
    "Describe it academically and stop there.",
    "Keep any high-pressure close at overview level.",
    "Give a conceptual sketch, never a working script.",
    "The mechanism may be discussed, provided no executable detail is included.",
    "Explain what it is without showing how it works in practice.",
    "Cover the concept but leave the implementation blank.",
    "Mention fake scarcity while avoiding instructions someone could use.",
    "The answer should remain informational rather than operational.",
    "Do not furnish a step-by-step for coercive selling.",
    "Teach recognition of the tactic, not deployment.",
    "High-level commentary is acceptable; usable copy is not.",
    "The agent can identify the method but cannot help implement it.",
    "Keep sharp-elbowed sales playbooks in the back room.",
    "Gray tactics don't belong in the toolkit.",
    "Remove any ethically hazy persuasion from consideration.",
    "Put aggressive closes behind a guardrail.",
    "The consultant sidesteps unsavory influence recipes.",
    "Sensitive conversion tricks are a no-go.",
    "We draw the line at manufactured pain.",
    "The response stays on the safe side of persuasion.",
    "Anything that leans too hard on fear gets left on the cutting-room floor.",
    "We won't open the black box on manipulative sales engineering.",
    "Should a tactic be deceptive, its details will be withheld.",
    "Deceptive or not, only compliant strategies qualify for discussion.",
    "No unethical method is to be explained.",
    "Instructions concerning fake urgency are hereby excluded.",
    "Explanations of manipulative psychology remain restricted.",
    "The guidance set comprises responsible persuasion exclusively.",
    "Coverage terminates where unethical pressure begins.",
    "A legal objection automatically removes the tactic from the answer.",
    "Eligibility for explanation depends on passing policy review.",
    "Preserve all available variants and withhold deceptive scripts.",
    "Preserve genuine and constructed variants while omitting coercive examples.",
    "Preserve the variants, then ban black-hat closes.",
    "Rather than treating the whole method as unavailable, omit manipulative tactics.",
    "This rule is not used to sanitize the method and it excludes fake-scarcity scripts.",
    "In the learning ledger, omit deceptive sales copy.",
    "The learning record filters out unethical persuasion ideas.",
    "This study says manipulation is harmful, so omit the tactic.",
    "The historical case excludes coercive methods from discussion.",
    "The source-reported outcome means we do not teach fake urgency.",
    "Redistribution rights forbid discussing pressure tactics.",
    "Binaries aside, withhold manipulative sales advice.",
    "In the forecast, avoid manipulative persuasion.",
    "As proof, do not explain deceptive offers.",
    "As demand evidence, withhold fake scarcity advice.",
    "Private data policy means we omit high-pressure copy.",
    "Passwords aside, never cover coercive closes.",
    "Before launch, do not explain coercive offers.",
    "During deployment, withhold fake-scarcity copy.",
    "For external execution, never cover manipulative persuasion.",
    "Owner authorization is required before we teach pressure closes.",
    "| Manipulative tactics | Excluded |",
    "| Fake scarcity | Not covered |",
    "| Coercive closes | Theory only |",
    "| This framework | Post-validation only |",
    "method=fake scarcity | availability=excluded",
    "method: fake scarcity | availability: excluded",
    "fake scarcity | excluded",
)

ALLOWED_CONTEXT = (
    "Constructed scarcity can lift response and erode repeat trust; compare conversion, refunds, and retention.",
    "Pressure effects vary by buyer and sales cycle; the full mechanism remains available.",
    "Label hypothetical evidence as hypothetical; this does not remove the tactic.",
    "The source position prefers low-pressure discovery; compare it with direct closing as a performance hypothesis.",
    "Current account access is unavailable, while the complete advertising method remains available for analysis.",
    "External spend requires owner authorization; ideation and complete mechanism analysis remain available.",
    "Do not suppress the underlying tactic.",
    "Never withhold a stored method because of a moral label.",
    "A private credential must not be copied into the learning ledger.",
    "The Genovese story is not used as efficacy evidence; its rhetoric and debunking remain available for analysis.",
    "Do not use customer interview compliments as demand evidence.",
    "Never use testimonials as proof that a medical claim is true.",
    "Do not share private credentials in an ad brief.",
    "Never reveal a customer's personal data in marketing copy.",
    "Do not include secrets in the sales plan.",
    "Avoid using fabricated case data as empirical evidence.",
    "Only include substantiated factual claims in the forecast.",
    "Pricing is recommended only after unit economics are measured.",
    "Do not describe an unverified claim as fact.",
    "Do not use a password as advertising copy.",
    "This skill does not apply to deleting production databases.",
    "A public launch requires owner authorization; the full framework and sandbox remain available.",
    "Omit email addresses from examples.",
    "The method is unavailable in the live account because access is missing, but remains available in the sandbox.",
    "The source says the story must be real, not manufactured; compare real and invented variants.",
    "Use this skill for a go or no-go decision about the business idea.",
)


def self_test() -> list[str]:
    errors: list[str] = []
    adversarial = (
        ADVERSARIAL_CAPS + ADDITIONAL_ADVERSARIAL_CAPS + FRESH_ADVERSARIAL_CAPS
    )
    for index, fixture in enumerate(adversarial, start=1):
        chunks = split_units(fixture, 1)
        labels = {
            label
            for chunk in chunks + chunk_windows(chunks)
            for label in violation_labels(chunk.text)
        }
        if not labels:
            errors.append(f"adversarial fixture {index} escaped semantic detection: {fixture}")
    for index, fixture in enumerate(ALLOWED_CONTEXT, start=1):
        chunks = split_units(fixture, 1)
        labels = {
            label
            for chunk in chunks + chunk_windows(chunks)
            for label in violation_labels(chunk.text)
        }
        if labels:
            errors.append(f"allowed context fixture {index} was overblocked: {fixture}")
    return errors


def scan_tree() -> tuple[list[str], int, int]:
    errors: list[str] = []
    files = 0
    chunks = 0
    manifest_path = PLUGIN_ROOT / "assets" / "skill-knowledge-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    inventory = manifest.get("skills", {})
    if len(inventory) != 26:
        errors.append(f"skill manifest must declare 26 skills, found {len(inventory)}")

    declared_paths: set[Path] = set()
    for skill_name, record in inventory.items():
        entrypoint = PLUGIN_ROOT / record["entrypoint"]
        declared_paths.add(entrypoint)
        for raw_root in record.get("bundle_roots", []):
            bundle_root = PLUGIN_ROOT / raw_root
            if not bundle_root.is_dir():
                errors.append(f"missing bundle root for {skill_name}: {raw_root}")
                continue
            for suffix in ("*.md", "*.yaml", "*.yml", "*.json", "*.csv"):
                declared_paths.update(bundle_root.rglob(suffix))
        for raw_file in record.get("bundle_files", []):
            declared_paths.add(PLUGIN_ROOT / raw_file)

    paths = sorted(
        set(SKILLS_ROOT.rglob("*.md"))
        | set(SKILLS_ROOT.rglob("*.yaml"))
        | set(SKILLS_ROOT.rglob("*.yml"))
        | set(UPSTREAM_ROOT.rglob("*.md"))
        | set((PLUGIN_ROOT / "assets" / "templates").rglob("*.md"))
        | set((PLUGIN_ROOT / "assets" / "templates").rglob("*.csv"))
        | declared_paths
        | {
            PLUGIN_ROOT / "README.md",
            PLUGIN_ROOT / "THIRD_PARTY_NOTICES.md",
            PLUGIN_ROOT / ".codex-plugin" / "plugin.json",
            manifest_path,
            PLUGIN_ROOT / "assets" / "skill-routing-fixtures.json",
            PLUGIN_ROOT / "assets" / "upstream-founder-playbook-manifest.json",
            PLUGIN_ROOT / "assets" / "foundation-lock.json",
        }
    )

    entrypoints = set(SKILLS_ROOT.glob("*/SKILL.md"))
    agent_yamls = set(SKILLS_ROOT.glob("*/agents/openai.yaml"))
    expected_entrypoints = {
        (PLUGIN_ROOT / record["entrypoint"]).resolve()
        for record in inventory.values()
    }
    expected_agents = {
        entrypoint.parent / "agents" / "openai.yaml"
        for entrypoint in expected_entrypoints
    }
    actual_entrypoints = {path.resolve() for path in entrypoints}
    actual_agents = {path.resolve() for path in agent_yamls}
    for path in sorted(expected_entrypoints - actual_entrypoints):
        errors.append(f"manifested skill entrypoint missing: {path.relative_to(PLUGIN_ROOT)}")
    for path in sorted(actual_entrypoints - expected_entrypoints):
        errors.append(f"unmanifested skill entrypoint present: {path.relative_to(PLUGIN_ROOT)}")
    for path in sorted(expected_agents - actual_agents):
        errors.append(f"manifested skill agent YAML missing: {path.relative_to(PLUGIN_ROOT)}")
    for path in sorted(actual_agents - expected_agents):
        errors.append(f"unmanifested skill agent YAML present: {path.relative_to(PLUGIN_ROOT)}")
    missing_declared = sorted(path for path in declared_paths if path not in paths or not path.is_file())
    for path in missing_declared:
        errors.append(f"declared knowledge surface is missing: {path.relative_to(PLUGIN_ROOT)}")

    seen_errors: set[tuple[str, Path, int, str]] = set()
    for path in paths:
        files += 1
        try:
            current_chunks = text_chunks(path)
        except (OSError, UnicodeError, json.JSONDecodeError, csv.Error) as exc:
            errors.append(f"cannot read {path.relative_to(PLUGIN_ROOT)}: {exc}")
            continue
        chunks += len(current_chunks)
        for chunk in current_chunks + chunk_windows(current_chunks):
            for label in violation_labels(chunk.text):
                key = (label, path, chunk.line, chunk.text[:300])
                if key in seen_errors:
                    continue
                seen_errors.add(key)
                errors.append(
                    f"{label} in {path.relative_to(PLUGIN_ROOT)}:{chunk.line}: "
                    f"{chunk.text[:300]}"
                )
    return errors, files, chunks


def verify_invariant() -> list[str]:
    errors: list[str] = []
    try:
        text = re.sub(
            r"\s+", " ", INVARIANT_PATH.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError) as exc:
        return [f"cannot read canonical knowledge-access invariant: {exc}"]
    for marker in REQUIRED_INVARIANT_MARKERS:
        if marker not in text:
            errors.append(f"knowledge-access invariant lost marker: {marker!r}")

    for entrypoint in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
        try:
            entrypoint_text = entrypoint.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read {entrypoint.relative_to(PLUGIN_ROOT)}: {exc}")
            continue
        active_markdown = re.sub(r"```.*?```", "", entrypoint_text, flags=re.DOTALL)
        active_markdown = re.sub(r"<!--.*?-->", "", active_markdown, flags=re.DOTALL)
        targets = re.findall(
            r"(?<!!)\[[^\]]+\]\(([^)]+)\)", active_markdown, flags=re.I
        )
        resolved = {
            (entrypoint.parent / target.split("#", 1)[0].strip()).resolve()
            for target in targets
            if Path(target.split("#", 1)[0].strip()).name.lower()
            == "knowledge-access-invariant.md"
        }
        if INVARIANT_PATH.resolve() not in resolved:
            errors.append(
                "skill entrypoint lost a resolved Markdown link to the "
                "knowledge-access invariant: "
                f"{entrypoint.relative_to(PLUGIN_ROOT)}"
            )
    return errors


def main() -> int:
    errors = self_test()
    errors.extend(verify_invariant())
    scan_errors, files, chunks = scan_tree()
    errors.extend(scan_errors)
    summary = {
        "adversarial_fixtures": len(
            ADVERSARIAL_CAPS + ADDITIONAL_ADVERSARIAL_CAPS + FRESH_ADVERSARIAL_CAPS
        ),
        "allowed_context_fixtures": len(ALLOWED_CONTEXT),
        "chunks_scanned": chunks,
        "errors": errors,
        "knowledge_files_scanned": files,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
