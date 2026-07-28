"""Input-side guardrail: flags likely prompt-injection attempts in the raw
user message *before* it reaches the LLM or any tool.

This is intentionally a pure, dependency-free function (no LLM call) so it's
fast, deterministic, and cheap to unit test. It is a first line of defense,
not a complete one — pair it with the system prompt's existing instruction to
ignore embedded instructions in tool results, and consider adding an
LLM-based classifier pass later for paraphrased/obfuscated attempts that slip
past these patterns.
"""

import re
from dataclasses import dataclass

# Each pattern targets a known injection family. Keep them named/grouped so a
# failing test tells you *which* family regressed, not just "injection.py
# broke".
_INSTRUCTION_OVERRIDE = [
    re.compile(r"ignore\s+(all\s+)?(the\s+)?(previous|prior|above)\s+instructions?", re.I),
    re.compile(r"disregard\s+(all\s+)?(the\s+)?(previous|prior|above)", re.I),
    re.compile(r"forget\s+(everything|all|your\s+instructions)", re.I),
    re.compile(r"new\s+instructions?\s*:", re.I),
    re.compile(r"override\s+(your|the|all)\s+(rules|instructions|policy|policies)", re.I),
]

_ROLE_HIJACK = [
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"act\s+as\s+(a|an|if)\s+", re.I),
    re.compile(r"pretend\s+(you|to)\s+(are|be)\s+", re.I),
    re.compile(r"from\s+now\s+on\s*,?\s+you", re.I),
    re.compile(r"\bDAN\b|do\s+anything\s+now", re.I),
    re.compile(r"jailbreak", re.I),
]

_SYSTEM_PROMPT_EXTRACTION = [
    re.compile(r"(reveal|show|print|repeat|output)\s+(your|the)\s+(system\s+)?prompt", re.I),
    re.compile(r"what\s+(are|is)\s+your\s+(system\s+)?instructions?", re.I),
    re.compile(r"repeat\s+everything\s+above", re.I),
]

_FAKE_DELIMITERS = [
    # Fake role/message boundary tags trying to smuggle a new turn.
    re.compile(r"</?\s*(system|assistant|developer)\s*>", re.I),
    re.compile(r"\[\s*(system|assistant|developer)\s*\]", re.I),
    re.compile(r"^\s*---+\s*$", re.M),
]

_PATTERN_GROUPS = {
    "instruction_override": _INSTRUCTION_OVERRIDE,
    "role_hijack": _ROLE_HIJACK,
    "system_prompt_extraction": _SYSTEM_PROMPT_EXTRACTION,
    "fake_delimiters": _FAKE_DELIMITERS,
}


@dataclass
class GuardrailResult:
    flagged: bool
    category: str | None = None
    matched_pattern: str | None = None


def check_prompt_injection(text: str) -> GuardrailResult:
    """Scan a single piece of user-supplied text for known injection patterns.

    Deliberately conservative: matches on well-established attack phrasing
    rather than broad topic filtering, to keep false positives low for
    legitimate onboarding questions (e.g. "what's HR's policy on X" should
    never trip this).
    """
    if not text or not text.strip():
        return GuardrailResult(flagged=False)

    for category, patterns in _PATTERN_GROUPS.items():
        for pattern in patterns:
            if pattern.search(text):
                return GuardrailResult(
                    flagged=True,
                    category=category,
                    matched_pattern=pattern.pattern,
                )

    return GuardrailResult(flagged=False)


def check_prompt_injection_history(texts: list[str]) -> GuardrailResult:
    """Scan a list of user-supplied texts (e.g. every HumanMessage in a
    checkpointed thread) and return the first match found.

    Used to catch a payload planted in an earlier turn that only becomes
    "active" once later context makes it relevant — a fresh-input-only check
    would miss this since the injection text isn't in the newest message.
    """
    for text in texts:
        result = check_prompt_injection(text)
        if result.flagged:
            return result
    return GuardrailResult(flagged=False)
