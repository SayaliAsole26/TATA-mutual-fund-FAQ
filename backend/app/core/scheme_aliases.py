"""Resolve scheme_id from user message text and alias map."""

from __future__ import annotations

import re

from app.core.corpus_registry import SchemeEntry, load_corpus_registry

# Alias token → scheme_id (lowercase keys)
SCHEME_ALIASES: dict[str, str] = {
    "elss": "tata-elss-fund-direct-growth",
    "tax saver": "tata-elss-fund-direct-growth",
    "silver": "tata-silver-etf-fof-direct-growth",
    "silver etf": "tata-silver-etf-fof-direct-growth",
    "digital india": "tata-digital-india-fund-direct-growth",
    "small cap": "tata-small-cap-fund-direct-growth",
    "large cap": "tata-large-cap-fund-direct-growth",
    "mid cap": "tata-mid-cap-direct-plan-growth",
    "flexi cap": "tata-flexi-cap-fund-direct-growth",
    "multicap": "tata-multicap-fund-direct-growth",
    "multi cap": "tata-multicap-fund-direct-growth",
    "floater": "tata-floater-fund-direct-growth",
    "arbitrage": "tata-arbitrage-fund-direct-growth",
    "ethical": "tata-ethical-fund-direct-growth",
    "ultra short": "tata-ultra-short-term-fund-direct-growth",
    "ultra short term": "tata-ultra-short-term-fund-direct-growth",
    "resources": "tata-resources-energy-fund-direct-growth",
    "energy": "tata-resources-energy-fund-direct-growth",
    "capital markets": "tata-nifty-capital-markets-index-fund-direct-growth",
    "sensex": "tata-bse-sensex-index-direct",
    "bse sensex": "tata-bse-sensex-index-direct",
}


def resolve_scheme(message: str) -> SchemeEntry | None:
    """Return the best matching scheme for a user message, or None."""
    text = message.strip()
    if not text:
        return None

    lowered = text.lower()
    schemes = load_corpus_registry()

    for scheme in schemes:
        if scheme.scheme_id in lowered:
            return scheme

    alias_hits: list[tuple[int, SchemeEntry]] = []
    for alias, scheme_id in SCHEME_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            scheme = next((s for s in schemes if s.scheme_id == scheme_id), None)
            if scheme:
                alias_hits.append((len(alias), scheme))

    if alias_hits:
        alias_hits.sort(key=lambda item: item[0], reverse=True)
        return alias_hits[0][1]

    name_hits: list[tuple[int, SchemeEntry]] = []
    for scheme in schemes:
        name = scheme.scheme_name.lower()
        if name in lowered:
            name_hits.append((len(name), scheme))

    if name_hits:
        name_hits.sort(key=lambda item: item[0], reverse=True)
        return name_hits[0][1]

    return None


def scheme_needs_clarification(message: str, scheme: SchemeEntry | None) -> bool:
    """True when the message looks scheme-specific but no scheme was resolved."""
    if scheme is not None:
        return False

    lowered = message.lower()
    scheme_cues = (
        "expense ratio",
        "exit load",
        "minimum sip",
        "min sip",
        "sip amount",
        "lumpsum",
        "benchmark",
        "fund manager",
        "who manages",
        "lock-in",
        "lock in",
        "nav",
        "aum",
        "fund size",
        "riskometer",
        "stamp duty",
        "tax implication",
        "investment objective",
        "ter",
        "annual fee",
    )
    return any(cue in lowered for cue in scheme_cues)
