"""Tests for semantic-first chunker (Phase 1.1.3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ingestion.chunker import (
    FALLBACK_SECTION_IDS,
    build_embed_text,
    chunk_scheme,
    estimate_tokens,
    extract_fallback_sections,
    save_scheme_chunks,
    split_long_text,
)

ELSS_CLEANED_SNIPPET = """
Exit load, stamp duty and tax
Exit load
Nil
Stamp duty on investment:
0.005% (from July 1st, 2020)
from July 1st 2020
Tax implication
If you redeem within one year, returns are taxed at 20%.
Check past data
Compare similar funds
Fund management
SJ
Sailesh Jain
Dec 2021
- Present
View details
Education
Mr. Jain is a Commerce Graduate.
Also manages these schemes
Tata Balanced Advantage Fund Direct Growth
Investment Objective
The scheme seeks long-term capital growth.
Fund benchmark
NIFTY 500 Total Return Index
"""


@pytest.fixture
def elss_processed() -> dict:
    return {
        "scheme_id": "tata-elss-fund-direct-growth",
        "scheme_name": "Tata ELSS Fund Direct Growth",
        "source_url": "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        "parsed_at": "2026-06-18T18:09:51+00:00",
        "sections": {
            "expense_ratio": "Expense ratio: 1.17%",
            "min_sip": "Minimum SIP amount: ₹500",
        },
        "structured_fields": {},
    }


def test_extract_fallback_sections_from_cleaned() -> None:
    sections = extract_fallback_sections(ELSS_CLEANED_SNIPPET)
    assert "exit_load" in sections
    assert "Nil" in sections["exit_load"]
    assert "tax" in sections
    assert "20%" in sections["tax"]
    assert "fund_managers" in sections
    assert "Sailesh Jain" in sections["fund_managers"]
    assert "investment_objective" in sections
    assert "long-term capital growth" in sections["investment_objective"]


def test_chunk_scheme_merges_processed_and_fallback(elss_processed: dict) -> None:
    chunks = chunk_scheme(
        "tata-elss-fund-direct-growth",
        processed=elss_processed,
        cleaned_text=ELSS_CLEANED_SNIPPET,
    )
    sections = {c.section for c in chunks}
    assert "expense_ratio" in sections
    assert "min_sip" in sections
    assert "exit_load" in sections
    assert "tax" in sections
    assert "fund_managers" in sections

    by_section = {c.section: c for c in chunks}
    assert by_section["expense_ratio"].chunk_source == "processed"
    assert by_section["exit_load"].chunk_source == "cleaned_fallback"


def test_processed_section_not_overwritten_by_fallback(elss_processed: dict) -> None:
    elss_processed["sections"]["exit_load"] = "Exit load: 0.25% within 7 days"
    chunks = chunk_scheme(
        "tata-elss-fund-direct-growth",
        processed=elss_processed,
        cleaned_text=ELSS_CLEANED_SNIPPET,
    )
    exit_chunks = [c for c in chunks if c.section == "exit_load"]
    assert len(exit_chunks) == 1
    assert "0.25%" in exit_chunks[0].content
    assert exit_chunks[0].chunk_source == "processed"


def test_chunk_metadata_fields(elss_processed: dict) -> None:
    chunks = chunk_scheme(
        "tata-elss-fund-direct-growth",
        processed=elss_processed,
        cleaned_text=ELSS_CLEANED_SNIPPET,
    )
    chunk = chunks[0]
    assert chunk.scheme_id == "tata-elss-fund-direct-growth"
    assert chunk.source_url.startswith("https://")
    assert chunk.extracted_at
    assert chunk.chunk_id.startswith("tata-elss-fund-direct-growth__")
    assert chunk.section_label


def test_build_embed_text_prefixes_short_chunks(elss_processed: dict) -> None:
    chunks = chunk_scheme(
        "tata-elss-fund-direct-growth",
        processed=elss_processed,
        cleaned_text="",
    )
    expense = next(c for c in chunks if c.section == "expense_ratio")
    embed_text = build_embed_text(expense)
    assert "Tata ELSS Fund Direct Growth" in embed_text
    assert "Expense ratio" in embed_text
    assert "1.17%" in embed_text


def test_split_long_text_under_limit() -> None:
    text = "Short factual sentence."
    assert split_long_text(text) == [text]


def test_split_long_text_produces_multiple_parts() -> None:
    sentence = "This is a sample sentence about mutual fund fees and charges. "
    text = sentence * 200
    parts = split_long_text(text)
    assert len(parts) > 1
    for part in parts:
        assert len(part) <= 450 * 4 + 50


def test_save_scheme_chunks(tmp_path: Path, elss_processed: dict) -> None:
    chunks = chunk_scheme(
        "tata-elss-fund-direct-growth",
        processed=elss_processed,
        cleaned_text=ELSS_CLEANED_SNIPPET,
    )
    out = save_scheme_chunks(
        chunks,
        "tata-elss-fund-direct-growth",
        path=tmp_path / "tata-elss-fund-direct-growth_chunks.json",
    )
    assert out.is_file()
    assert out.name == "tata-elss-fund-direct-growth_chunks.json"


def test_chunk_real_elss_processed_data() -> None:
    """Integration: use committed processed + cleaned files when present."""
    from config.settings import get_settings

    settings = get_settings()
    processed_path = settings.processed_dir / "tata-elss-fund-direct-growth.json"
    cleaned_path = settings.raw_dir / "tata-elss-fund-direct-growth.cleaned.txt"
    if not processed_path.is_file() or not cleaned_path.is_file():
        pytest.skip("local corpus files not available")

    chunks = chunk_scheme("tata-elss-fund-direct-growth", settings=settings)
    assert len(chunks) >= 10
    sections = {c.section for c in chunks}
    for required in ("expense_ratio", "min_sip", "exit_load", "tax", "fund_managers"):
        assert required in sections


def test_fallback_section_ids_are_subset_of_parser_sections() -> None:
    from app.ingestion.parser import SECTION_IDS

    assert FALLBACK_SECTION_IDS.issubset(set(SECTION_IDS))


def test_chunk_and_save_scheme(tmp_path: Path, elss_processed: dict) -> None:
    class FakeSettings:
        processed_dir = tmp_path

    from app.ingestion.chunker import chunk_and_save_scheme

    chunks, path = chunk_and_save_scheme(
        "tata-elss-fund-direct-growth",
        settings=FakeSettings(),  # type: ignore[arg-type]
        processed=elss_processed,
        cleaned_text=ELSS_CLEANED_SNIPPET,
    )
    assert len(chunks) >= 5
    assert path == tmp_path / "tata-elss-fund-direct-growth_chunks.json"
    assert path.is_file()


def test_estimate_tokens() -> None:
    assert estimate_tokens("abcd") >= 1
    assert estimate_tokens("") == 0
