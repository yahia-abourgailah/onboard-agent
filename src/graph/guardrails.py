"""Input-side guardrail: flags likely prompt-injection attempts in the raw
user message *before* it reaches the LLM or any tool.

This is intentionally a pure, dependency-free function (no LLM call) so it's
fast, deterministic, and cheap to unit test. It is a first line of defense,
not a complete one — pair it with the system prompt's existing instruction to
ignore embedded instructions in tool results, and consider adding an
LLM-based classifier pass later for paraphrased/obfuscated attempts that slip
past these patterns.

Language coverage: the agent answers in English, Arabic and Franco-Arabic
(Arabizi), so the patterns below cover all three. Arabic and Franco coverage
is necessarily thinner than English — Franco has no fixed orthography, so the
same phrase has many spellings and a regex set can only catch the common
ones. Treat non-English coverage as best-effort; an LLM classifier is the
real answer if this becomes a genuine attack surface.

Tuning note: patterns are deliberately narrow. A false positive here refuses
a real employee's onboarding question, which is a worse everyday outcome than
missing one paraphrased attack that the system prompt's own rules still
defend against. Anything matching ordinary onboarding phrasing ("act as a
guide for my first day", "what are your instructions for new hires") must not
trip these.
"""

import re
from dataclasses import dataclass

# Alef appears as bare/hamza/madda forms and users type all of them
# interchangeably, so match the whole family wherever a word starts with one.
_ALEF = r"[أإآا]"

# Each pattern targets a known injection family. Keep them named/grouped so a
# failing test tells you *which* family regressed, not just "injection.py
# broke".
_INSTRUCTION_OVERRIDE = [
    re.compile(r"ignore\s+(all\s+)?(the\s+)?(previous|prior|above)\s+instructions?", re.I),
    re.compile(r"disregard\s+(all\s+)?(the\s+)?(previous|prior|above)", re.I),
    re.compile(r"forget\s+(everything|all|your\s+instructions)", re.I),
    re.compile(r"new\s+instructions?\s*:", re.I),
    re.compile(r"override\s+(your|the|all)\s+(rules|instructions|policy|policies)", re.I),
    # Arabic: "تجاهل التعليمات/الأوامر", "انسى كل التعليمات", "تعليمات جديدة:"
    re.compile(r"تجاهل\s+(كل\s+)?(ال)?(تعليمات|أوامر|اوامر|قواعد)"),
    re.compile(rf"{_ALEF}نس[ىي]?\s+(كل\s+)?(ال)?(تعليمات|أوامر|اوامر|قواعد)"),
    re.compile(r"(تعليمات|أوامر|اوامر)\s+جديدة\s*:"),
    # Franco-Arabic: "tagahel el instructions", "ensa el rules", "mate3melsh el rules"
    re.compile(r"\b(tagahel|tag2ahel|etgahel|itgahel)\b", re.I),
    re.compile(r"\b(ensa|insa|ensi)\s+(kol\s+)?(el\s+)?(instructions|rules|awamer|ta3limat)", re.I),
    re.compile(r"\bmate3melsh\s+(el\s+)?(instructions|rules|awamer|ta3limat)", re.I),
]

_ROLE_HIJACK = [
    re.compile(r"you\s+are\s+now\s+", re.I),
    # Narrowed: only role *reassignment* onto an AI persona. Bare "act as a
    # guide/mentor" is legitimate onboarding phrasing and must not match.
    re.compile(
        r"\bact\s+as\s+(an?\s+)?(ai\b|assistant|chatbot|language\s+model|model\b|dan\b)",
        re.I,
    ),
    re.compile(r"pretend\s+(you|to)\s+(are|be)\s+", re.I),
    re.compile(r"from\s+now\s+on\s*,?\s+you", re.I),
    re.compile(r"\bDAN\b|do\s+anything\s+now", re.I),
    re.compile(r"jailbreak", re.I),
    # Arabic: "أنت الآن ...", "تظاهر أنك ...", "بدون قيود"
    re.compile(rf"{_ALEF}نت\s+(ال[آا]ن|دلوقت[يى])"),
    re.compile(rf"تظاهر\s+{_ALEF}ن[كك]"),
    re.compile(r"بدون\s+(قيود|حدود|قواعد)"),
    # Franco-Arabic: "enta delwa2ty assistant tany"
    re.compile(r"\benta\s+(delwa2ty|dlw2ty|dilwa2ty|dlwa2ty)\b", re.I),
]

_SYSTEM_PROMPT_EXTRACTION = [
    re.compile(r"(reveal|show|print|repeat|output)\s+(your|the)\s+(system\s+)?prompt", re.I),
    # Narrowed with an explicit qualifier: "what are your instructions for new
    # hires?" is a real question an intern asks and must not match.
    re.compile(
        r"what\s+(are|is)\s+your\s+(system|original|initial|exact|full)\s+(prompt|instructions?)",
        re.I,
    ),
    re.compile(r"repeat\s+everything\s+above", re.I),
    # Arabic: "اظهر البرومبت", "ما هي تعليماتك"
    re.compile(rf"({_ALEF}ظهر|{_ALEF}كتب|كرر)\s+(ال)?(برومبت|بروبت|تعليمات)"),
    re.compile(r"ما\s+ه[يى]\s+تعليمات[كك]"),
]

_FAKE_DELIMITERS = [
    # Fake role/message boundary tags trying to smuggle a new turn.
    # NOTE: a bare "---" line was previously matched here and removed — it
    # flagged ordinary Markdown horizontal rules in legitimate messages, and
    # the explicit role tags below cover the realistic version of this attack.
    re.compile(r"</?\s*(system|assistant|developer)\s*>", re.I),
    re.compile(r"\[\s*(system|assistant|developer)\s*\]", re.I),
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
    """Scan several user-supplied texts and return the first match found.

    NOTE: this is NOT what the graph's input_guard uses, and it must not be
    used to screen checkpointed history on every turn. Doing so permanently
    bricks a thread: the offending message stays in history, so every later
    innocent turn re-matches it and gets refused, with no way back except
    starting a new conversation.

    The graph instead screens each incoming message once and *deletes* a
    flagged one from the thread (see graph/nodes.py), which gives the same
    protection against a dormant payload without the poisoning. This helper
    is kept for callers that need to scan a standalone batch of text.
    """
    for text in texts:
        result = check_prompt_injection(text)
        if result.flagged:
            return result
    return GuardrailResult(flagged=False)
