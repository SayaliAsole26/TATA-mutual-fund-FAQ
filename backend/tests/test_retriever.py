"""Tests for hybrid retriever (Phase 2a)."""

from __future__ import annotations

import pytest

from app.core.corpus_registry import get_scheme_by_id
from app.core.intent import detect_intent_section
from app.core.retriever import retrieve
from app.ingestion.embed_index import stats
from config.settings import get_settings


@pytest.fixture
def elss_scheme():
    scheme = get_scheme_by_id("tata-elss-fund-direct-growth")
    assert scheme is not None
    return scheme


def test_retrieve_structured_min_sip(elss_scheme) -> None:
    settings = get_settings()
    if not settings.schemes_metadata_path.is_file():
        pytest.skip("schemes.json not available")

    result = retrieve(
        "What is the minimum SIP?",
        elss_scheme,
        intent_section="min_sip",
    )
    assert result.chunks
    assert result.source == "structured"
    assert result.chunks[0].section == "min_sip"
    assert "₹500" in result.chunks[0].content


def test_retrieve_vector_expense_ratio_integration(elss_scheme) -> None:
    if stats().get("status") != "ok":
        pytest.skip("vector index not built")

    result = retrieve(
        "What is the expense ratio for this scheme?",
        elss_scheme,
        intent_section="expense_ratio",
    )
    assert result.chunks
    assert result.chunks[0].section in {"expense_ratio", "expense_ratio"}
    assert "%" in result.chunks[0].content or "Expense ratio" in result.chunks[0].content


def test_detect_and_retrieve_fund_managers() -> None:
    scheme = get_scheme_by_id("tata-flexi-cap-fund-direct-growth")
    assert scheme is not None
    if stats().get("status") != "ok":
        pytest.skip("vector index not built")

    query = "Who manages Tata Flexi Cap Fund?"
    section = detect_intent_section(query)
    result = retrieve(query, scheme, intent_section=section)
    assert result.chunks
    assert any(c.section == "fund_managers" for c in result.chunks)
