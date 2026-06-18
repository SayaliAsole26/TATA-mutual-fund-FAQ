"""Tests for ingestion parser (Phase 1.1.3)."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.ingestion.fetcher import FetchedContent
from app.ingestion.parser import parse_scheme_content


@pytest.fixture
def elss_fetched() -> FetchedContent:
    path = Path(__file__).parent / "fixtures" / "tata-elss-fund-direct-growth.md"
    content = path.read_text(encoding="utf-8")
    return FetchedContent(
        scheme_id="tata-elss-fund-direct-growth",
        source_url="https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        content=content,
        fetched_at=datetime.now(timezone.utc),
        from_snapshot=True,
    )


@pytest.fixture
def sensex_fetched() -> FetchedContent:
    path = Path(__file__).parent / "fixtures" / "tata-bse-sensex-index-direct.md"
    content = path.read_text(encoding="utf-8")
    return FetchedContent(
        scheme_id="tata-bse-sensex-index-direct",
        source_url="https://groww.in/mutual-funds/tata-bse-sensex-index-direct",
        content=content,
        fetched_at=datetime.now(timezone.utc),
        from_snapshot=True,
    )


def test_parse_elss_expense_ratio(elss_fetched: FetchedContent) -> None:
    parsed = parse_scheme_content(elss_fetched)
    assert parsed.structured_fields["expense_ratio"] == "1.17%"


def test_parse_elss_min_sip(elss_fetched: FetchedContent) -> None:
    parsed = parse_scheme_content(elss_fetched)
    assert parsed.structured_fields["min_sip"] == "₹500"


def test_parse_elss_exit_load(elss_fetched: FetchedContent) -> None:
    parsed = parse_scheme_content(elss_fetched)
    assert parsed.structured_fields["exit_load"] == "Nil"


def test_parse_elss_benchmark(elss_fetched: FetchedContent) -> None:
    parsed = parse_scheme_content(elss_fetched)
    assert "NIFTY 500" in parsed.structured_fields["benchmark"]


def test_parse_elss_riskometer(elss_fetched: FetchedContent) -> None:
    parsed = parse_scheme_content(elss_fetched)
    assert "Very High" in parsed.structured_fields["riskometer"]


def test_parse_elss_lock_in(elss_fetched: FetchedContent) -> None:
    parsed = parse_scheme_content(elss_fetched)
    assert "3Y" in parsed.structured_fields["elss_lock_in"]


def test_parse_elss_tax(elss_fetched: FetchedContent) -> None:
    parsed = parse_scheme_content(elss_fetched)
    assert "taxed" in parsed.structured_fields["tax"].lower()


def test_parse_elss_fund_managers(elss_fetched: FetchedContent) -> None:
    parsed = parse_scheme_content(elss_fetched)
    assert "Sailesh Jain" in parsed.structured_fields["fund_managers"]


def test_parse_elss_sections_populated(elss_fetched: FetchedContent) -> None:
    parsed = parse_scheme_content(elss_fetched)
    for key in (
        "expense_ratio",
        "exit_load",
        "min_sip",
        "riskometer",
        "benchmark",
        "fund_managers",
        "tax",
        "elss_lock_in",
    ):
        assert key in parsed.sections
        assert parsed.sections[key]


def test_parse_sensex_exit_load(sensex_fetched: FetchedContent) -> None:
    parsed = parse_scheme_content(sensex_fetched)
    assert "0.25%" in parsed.structured_fields["exit_load"]


def test_parse_sensex_min_sip(sensex_fetched: FetchedContent) -> None:
    parsed = parse_scheme_content(sensex_fetched)
    assert parsed.structured_fields["min_sip"] == "₹150"


def test_parse_scheme_name(elss_fetched: FetchedContent) -> None:
    parsed = parse_scheme_content(elss_fetched)
    assert parsed.scheme_name == "Tata ELSS Fund Direct Growth"
