"""Tests for response formatter (Phase 2)."""

from app.core.formatter import (
    build_formatted_answer,
    format_footer_date,
    is_allowed_source_url,
    normalize_llm_output,
)
from app.core.retriever import RetrievedChunk


def test_format_footer_date() -> None:
    assert format_footer_date("2026-06-18T18:09:51+00:00") == "18 Jun 2026"


def test_build_formatted_answer() -> None:
    text = build_formatted_answer(
        "The minimum SIP amount is ₹500.",
        "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        "2026-06-18T18:09:51+00:00",
    )
    assert "Source: https://groww.in/mutual-funds/tata-elss-fund-direct-growth" in text
    assert "Last updated from sources: 18 Jun 2026" in text


def test_allowed_source_url() -> None:
    assert is_allowed_source_url("https://groww.in/mutual-funds/tata-elss-fund-direct-growth")
    assert not is_allowed_source_url("https://example.com/bad")


def test_normalize_llm_output_fixes_bad_url() -> None:
    raw = (
        "The expense ratio is 1.17%.\n\n"
        "Source: https://evil.example.com\n\n"
        "Last updated from sources: 18 Jun 2026"
    )
    fixed = normalize_llm_output(
        raw,
        "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        "2026-06-18T18:09:51+00:00",
    )
    assert "groww.in/mutual-funds/tata-elss-fund-direct-growth" in fixed


def test_format_from_structured_chunk() -> None:
    chunk = RetrievedChunk(
        chunk_id="x",
        content="Minimum SIP amount: ₹500",
        section="min_sip",
        scheme_id="tata-elss-fund-direct-growth",
        scheme_name="Tata ELSS Fund Direct Growth",
        source_url="https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        extracted_at="2026-06-18T18:09:51+00:00",
    )
    from app.core.formatter import format_from_structured

    answer = format_from_structured(chunk, "min sip?")
    assert "₹500" in answer
    assert "Source:" in answer
