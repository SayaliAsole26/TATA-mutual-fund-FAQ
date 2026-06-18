"""Input guardrails and output validation (Phase 3)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.formatter import (
    count_answer_sentences,
    extract_answer_body,
    extract_source_url,
    has_valid_footer,
    is_allowed_citation_url,
    truncate_answer_body,
)

# --- PII patterns (conservative) ---

PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
AADHAAR_PATTERN = re.compile(r"\b(?:aadhaar|aadhar)\s*(?:number|no\.?)?\s*(\d{4}\s?\d{4}\s?\d{4}|\d{12})\b", re.I)
AADHAAR_STANDALONE = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b")
OTP_PATTERN = re.compile(r"\b(?:otp|one[- ]time password)\s*[:#]?\s*\d{4,8}\b", re.I)
ACCOUNT_PATTERN = re.compile(
    r"\b(?:account|acct|folio|ucc)\s*(?:number|no\.?|#)?\s*[:#]?\s*[\d/\-]{6,}\b",
    re.I,
)

# --- Input policy patterns ---

ADVISORY_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\bshould\s+i\b",
        r"\b(?:do|would)\s+you\s+recommend\b",
        r"\brecommend(?:ation)?\b",
        r"\bworth\s+investing\b",
        r"\bgood\s+investment\b",
        r"\bbuy\s+or\s+sell\b",
        r"\bwhen\s+should\s+i\s+sell\b",
        r"\bwhich\s+fund\s+(?:should|do)\s+i\b",
        r"\bsuits?\s+a\s+(?:conservative|aggressive|young|retired)\b",
        r"\bignore\s+(?:all\s+)?(?:previous|prior)\s+instructions\b",
        r"\b(?:pretend|act)\s+(?:you\s+are|as)\s+(?:a\s+)?financial\s+advisor\b",
        r"\bwill\s+i\s+be\s+rich\b",
        r"\bis\s+it\s+(?:bad|good)\s+to\s+(?:not\s+)?invest\b",
        r"\brisk[- ]free\b",
        r"\bworth\s+buying\b",
        r"\bshould\s+i\s+invest\b",
    )
)

COMPARATIVE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\bbetter\s+than\b",
        r"\bcompare\b",
        r"\b(?:vs\.?|versus)\b",
        r"\bwhich\s+(?:fund\s+)?is\s+best\b",
        r"\bwhich\s+fund\s+is\s+better\b",
        r"\brank(?:ing)?\s+(?:the\s+)?(?:\d+\s+)?(?:tata\s+)?funds?\b",
        r"\bbest\s+(?:tata\s+)?fund\b",
        r"\bbeat\s+(?:the\s+)?category\b",
    )
)

PERFORMANCE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\b\d[\d-]*[-\s]*(?:year|yr|month|week|day)s?\s+return\b",
        r"\b(?:1|3|5|10)[\s-]*(?:year|yr)\s+return\b",
        r"\b(?:annual|historical|past)\s+return\b",
        r"\breturn(?:s)?\s+(?:of|for|did)\b",
        r"\bwhat\s+(?:was|were)\s+the\s+return\b",
        r"\breturns?\s+did\b",
        r"\blast\s+year(?:'s)?\s+return\b",
        r"\breturn(?:s)?\s+.*\blast\s+year\b",
        r"\bcagr\b",
        r"\bxirr\b",
        r"\bperformance\s+(?:of|for)\b",
        r"\bupward\s+trend\b",
        r"\bdownward\s+trend\b",
        r"\b(?:predict|forecast)\s+(?:the\s+)?nav\b",
        r"\bnav\s+(?:next|tomorrow|prediction)\b",
        r"\bhow\s+much\s+(?:did\s+it\s+)?(?:gain|lose|grow)\b",
    )
)

OTHER_AMC_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\bhdfc\b",
        r"\bsbi\b",
        r"\bicici\b",
        r"\baxis\b",
        r"\bnippon\b",
        r"\bmirae\b",
        r"\bparag\s+parikh\b",
        r"\buti\b",
        r"\baditya\s+birla\b",
        r"\bkotak\b",
        r"\bfranklin\b",
    )
)

OUT_OF_SCOPE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\bweather\b",
        r"\bopen\s+(?:a\s+)?groww\s+account\b",
        r"\bwho\s+won\s+the\s+(?:match|game|election)\b",
    )
)

OUTPUT_ADVICE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\byou\s+should\s+invest\b",
        r"\bi\s+recommend\b",
        r"\bbetter\s+(?:fund|option|choice)\b",
        r"\bworth\s+investing\b",
        r"\bgood\s+investment\b",
        r"\bbuy\s+this\s+fund\b",
        r"\bsell\s+this\s+fund\b",
    )
)

OUTPUT_COMPARISON_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\bbetter\s+than\b",
        r"\bcompare(?:d)?\s+to\b",
        r"\boutperform\b",
        r"\bunderperform\b",
        r"\brank(?:ing)?\b",
    )
)

OUTPUT_PERFORMANCE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\b\d+(?:\.\d+)?%\s+return\b",
        r"\breturn(?:ed)?\s+\d+(?:\.\d+)?%",
        r"\bcagr\s+(?:of|is)\s+\d",
        r"\bxirr\s+(?:of|is)\s+\d",
        r"\boutperformed\b",
    )
)


@dataclass
class InputGuardrailResult:
    blocked: bool = False
    reason: str | None = None


@dataclass
class OutputValidationResult:
    valid: bool = True
    issues: list[str] = field(default_factory=list)


def contains_pii(message: str) -> bool:
    if PAN_PATTERN.search(message):
        return True
    if AADHAAR_PATTERN.search(message) or AADHAAR_STANDALONE.search(message):
        return True
    if EMAIL_PATTERN.search(message):
        return True
    if PHONE_PATTERN.search(message):
        return True
    if OTP_PATTERN.search(message):
        return True
    if ACCOUNT_PATTERN.search(message):
        return True
    return False


def _matches_any(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def is_advisory_query(message: str) -> bool:
    return _matches_any(message, ADVISORY_PATTERNS)


def is_comparative_query(message: str) -> bool:
    return _matches_any(message, COMPARATIVE_PATTERNS)


def is_performance_query(message: str) -> bool:
    return _matches_any(message, PERFORMANCE_PATTERNS)


def is_out_of_corpus_query(message: str) -> bool:
    if not _matches_any(message, OTHER_AMC_PATTERNS):
        return False
    lowered = message.lower()
    if re.search(r"\btata\b", lowered):
        return False
    # Other AMC named without Tata — out of corpus even if a generic alias would match.
    return True


def is_out_of_scope_query(message: str) -> bool:
    return _matches_any(message, OUT_OF_SCOPE_PATTERNS)


def classify_input(message: str) -> InputGuardrailResult:
    """
    Pre-retrieval input guardrails. Order: PII → advisory → comparative →
    out-of-corpus → out-of-scope → performance.
    """
    if contains_pii(message):
        return InputGuardrailResult(blocked=True, reason="pii")

    if is_advisory_query(message):
        return InputGuardrailResult(blocked=True, reason="advisory")

    if is_comparative_query(message):
        return InputGuardrailResult(blocked=True, reason="comparative")

    if is_out_of_corpus_query(message):
        return InputGuardrailResult(blocked=True, reason="out_of_corpus")

    if is_out_of_scope_query(message):
        return InputGuardrailResult(blocked=True, reason="out_of_scope")

    if is_performance_query(message):
        return InputGuardrailResult(blocked=True, reason="performance")

    return InputGuardrailResult()


def validate_output(answer_text: str) -> OutputValidationResult:
    """Post-generation factual answer validation."""
    issues: list[str] = []
    body = extract_answer_body(answer_text)

    if count_answer_sentences(answer_text) > 3:
        issues.append("too_many_sentences")

    source_url = extract_source_url(answer_text)
    if not source_url:
        issues.append("missing_source_url")
    elif not is_allowed_citation_url(source_url):
        issues.append("disallowed_source_url")

    if not has_valid_footer(answer_text):
        issues.append("invalid_footer")

    if _matches_any(body, OUTPUT_ADVICE_PATTERNS):
        issues.append("advice_language")

    if _matches_any(body, OUTPUT_COMPARISON_PATTERNS):
        issues.append("comparison_language")

    if _matches_any(body, OUTPUT_PERFORMANCE_PATTERNS):
        issues.append("performance_claim")

    return OutputValidationResult(valid=not issues, issues=issues)


def repair_output(answer_text: str, *, fallback_url: str, fallback_date: str) -> str:
    """Best-effort repair: truncate sentences and fix citation/footer."""
    from app.core.formatter import build_formatted_answer, normalize_llm_output

    body = truncate_answer_body(answer_text, max_sentences=3)
    repaired = build_formatted_answer(body, fallback_url, fallback_date)
    return normalize_llm_output(repaired, fallback_url, fallback_date)
