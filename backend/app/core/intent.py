"""Map user questions to FAQ section ids."""

from __future__ import annotations

import re

from app.ingestion.parser import SECTION_IDS

# (section_id, patterns) — first match wins (order matters)
INTENT_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("exit_load", ("exit load", "redemption charge", "redemption fee")),
    ("expense_ratio", ("expense ratio", "ter", "annual fee", "management fee")),
    ("min_sip", ("minimum sip", "min sip", "min. for sip", "sip amount", "monthly sip")),
    ("min_lumpsum", ("minimum lumpsum", "min lumpsum", "first investment", "lumpsum")),
    ("fund_managers", ("fund manager", "who manages", "managed by", "portfolio manager")),
    ("tax", ("tax implication", "taxation", "tax on", "redeem tax", "capital gains tax")),
    ("stamp_duty", ("stamp duty",)),
    ("benchmark", ("benchmark", "tracks", "index tracked")),
    ("elss_lock_in", ("lock-in", "lock in", "elss lock")),
    ("investment_objective", ("investment objective", "objective of the fund")),
    ("riskometer", ("riskometer", "risk rating", "risk level")),
    ("nav", (r"\bnav\b", "net asset value", "latest nav")),
    ("aum", ("aum", "fund size", "assets under management")),
)


def detect_intent_section(message: str) -> str | None:
    """Return section id if intent is confident, else None."""
    lowered = message.lower()
    for section_id, patterns in INTENT_PATTERNS:
        for pattern in patterns:
            if pattern.startswith(r"\b"):
                if re.search(pattern, lowered):
                    return section_id
            elif pattern in lowered:
                return section_id
    return None


def is_nav_query(message: str) -> bool:
    lowered = message.lower()
    return bool(re.search(r"\bnav\b", lowered)) or "net asset value" in lowered


def sections_for_broad_search(intent_section: str | None) -> int:
    """k for tier-3 broad vector search."""
    if intent_section in {"tax", "fund_managers", "investment_objective"}:
        return 5
    return 3


STRUCTURED_FIELDS = frozenset(
    {
        "expense_ratio",
        "min_sip",
        "min_lumpsum",
        "exit_load",
        "benchmark",
        "riskometer",
        "nav",
        "aum",
        "stamp_duty",
        "elss_lock_in",
        "fund_managers",
        "tax",
    }
)


def is_structured_section(section: str | None) -> bool:
    return section is not None and section in STRUCTURED_FIELDS and section in SECTION_IDS
