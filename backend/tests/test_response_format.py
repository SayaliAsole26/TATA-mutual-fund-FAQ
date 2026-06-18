"""Response format validation tests (Phase 5)."""

from __future__ import annotations

import re

from app.core.formatter import (
    build_formatted_answer,
    count_answer_sentences,
    extract_answer_body,
    extract_source_url,
    has_valid_footer,
    is_allowed_citation_url,
    is_allowed_source_url,
)
from app.core.guardrails import validate_output

SOURCE_LINE = re.compile(r"^Source:\s+https://", re.MULTILINE)
FOOTER_LINE = re.compile(r"^Last updated from sources:\s+.+$", re.MULTILINE)


def test_answer_has_single_source_line() -> None:
    answer = build_formatted_answer(
        "The minimum SIP amount is ₹500.",
        "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        "2026-06-18T18:09:51+00:00",
    )
    assert len(SOURCE_LINE.findall(answer)) == 1
    assert len(FOOTER_LINE.findall(answer)) == 1


def test_extract_source_and_footer() -> None:
    answer = build_formatted_answer(
        "The expense ratio is 1.17%.",
        "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        "2026-06-18T18:09:51+00:00",
    )
    url = extract_source_url(answer)
    assert url == "https://groww.in/mutual-funds/tata-elss-fund-direct-growth"
    assert is_allowed_source_url(url)
    assert has_valid_footer(answer)
    assert count_answer_sentences(answer) <= 3


def test_citation_url_must_be_corpus_or_educational() -> None:
    groww = "https://groww.in/mutual-funds/tata-elss-fund-direct-growth"
    assert is_allowed_citation_url(groww)
    assert is_allowed_citation_url("https://www.amfiindia.com/investor-corner")
    assert not is_allowed_citation_url("https://example.com/fund")


def test_validate_rejects_missing_footer() -> None:
    broken = "The minimum SIP amount is ₹500.\n\nSource: https://groww.in/mutual-funds/tata-elss-fund-direct-growth"
    result = validate_output(broken)
    assert result.valid is False


def test_validate_rejects_advice_language_in_body() -> None:
    answer = build_formatted_answer(
        "You should buy this fund today for guaranteed returns.",
        "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        "2026-06-18T18:09:51+00:00",
    )
    result = validate_output(answer)
    assert result.valid is False
    assert "advice_language" in result.issues


def test_answer_body_excludes_source_block() -> None:
    answer = build_formatted_answer(
        "Lock-in period is 3 years.",
        "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        "2026-06-18T18:09:51+00:00",
    )
    body = extract_answer_body(answer)
    assert "Source:" not in body
    assert "Last updated" not in body
