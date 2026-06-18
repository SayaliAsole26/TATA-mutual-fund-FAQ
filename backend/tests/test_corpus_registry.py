"""Tests for corpus registry (Phase 1.1.2)."""

from pathlib import Path

import pytest

from app.core.corpus_registry import load_corpus_registry
from config.settings import get_settings

EXPECTED_SCHEME_IDS = {
    "tata-small-cap-fund-direct-growth",
    "tata-digital-india-fund-direct-growth",
    "tata-silver-etf-fof-direct-growth",
    "tata-ethical-fund-direct-growth",
    "tata-arbitrage-fund-direct-growth",
    "tata-nifty-capital-markets-index-fund-direct-growth",
    "tata-resources-energy-fund-direct-growth",
    "tata-elss-fund-direct-growth",
    "tata-multicap-fund-direct-growth",
    "tata-ultra-short-term-fund-direct-growth",
    "tata-mid-cap-direct-plan-growth",
    "tata-flexi-cap-fund-direct-growth",
    "tata-large-cap-fund-direct-growth",
    "tata-floater-fund-direct-growth",
    "tata-bse-sensex-index-direct",
}


@pytest.fixture
def registry_path() -> Path:
    return get_settings().corpus_registry_path


def test_registry_has_fifteen_schemes(registry_path: Path) -> None:
    schemes = load_corpus_registry(registry_path)
    assert len(schemes) == 15


def test_registry_scheme_ids(registry_path: Path) -> None:
    schemes = load_corpus_registry(registry_path)
    assert {s.scheme_id for s in schemes} == EXPECTED_SCHEME_IDS


def test_registry_required_fields(registry_path: Path) -> None:
    schemes = load_corpus_registry(registry_path)
    for scheme in schemes:
        assert scheme.amc == "Tata Mutual Fund"
        assert scheme.scheme_name
        assert scheme.source_url.startswith("https://groww.in/mutual-funds/")
        assert scheme.category
        assert scheme.last_ingested_at is None or isinstance(scheme.last_ingested_at, str)


def test_registry_urls_are_unique(registry_path: Path) -> None:
    schemes = load_corpus_registry(registry_path)
    urls = [s.source_url for s in schemes]
    assert len(urls) == len(set(urls))
