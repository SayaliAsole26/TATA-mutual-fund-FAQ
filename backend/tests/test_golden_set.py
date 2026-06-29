"""Golden-set factual and refusal QA tests (Phase 5)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.core.formatter import count_answer_sentences, extract_source_url, is_allowed_source_url
from app.core.orchestrator import handle_chat
from app.core.templates import AMFI_INVESTOR_CORNER, SEBI_INVESTOR_EDUCATION
from app.ingestion.embed_index import stats


@dataclass(frozen=True)
class GoldenCase:
    question: str
    scheme_id: str
    url_part: str
    must_contain: tuple[str, ...] = ()


GOLDEN_FACTUAL: tuple[GoldenCase, ...] = (
    GoldenCase("Minimum SIP for Tata ELSS?", "tata-elss-fund-direct-growth", "tata-elss", ("₹500",)),
    GoldenCase("What is the exit load on Tata Arbitrage Fund?", "tata-arbitrage-fund-direct-growth", "tata-arbitrage", ("exit load", "0.25%")),
    GoldenCase("Benchmark for Tata BSE Sensex Index?", "tata-bse-sensex-index-direct", "tata-bse-sensex", ("Sensex",)),
    GoldenCase("Expense ratio of Tata Silver ETF FoF?", "tata-silver-etf-fof-direct-growth", "tata-silver-etf-fof", ("0.21%",)),
    GoldenCase("Risk level of Tata Small Cap Fund?", "tata-small-cap-fund-direct-growth", "tata-small-cap", ("Very High",)),
    GoldenCase("Who are the fund managers of Tata Multicap Fund?", "tata-multicap-fund-direct-growth", "tata-multicap", ("Fund manager", "Meeta")),
    GoldenCase("Minimum lumpsum for Tata Large Cap?", "tata-large-cap-fund-direct-growth", "tata-large-cap", ("₹5,000",)),
    GoldenCase("ELSS lock-in for Tata ELSS?", "tata-elss-fund-direct-growth", "tata-elss", ("3", "lock")),
    GoldenCase("Expense ratio for Tata Flexi Cap?", "tata-flexi-cap-fund-direct-growth", "tata-flexi-cap", ("0.68%",)),
    GoldenCase("What is the minimum SIP for Tata Mid Cap Fund?", "tata-mid-cap-direct-plan-growth", "tata-mid-cap", ("₹100",)),
    GoldenCase("Benchmark for Tata Digital India Fund?", "tata-digital-india-fund-direct-growth", "tata-digital-india", ("NIFTY IT",)),
    GoldenCase("What is the expense ratio for Tata Floater Fund?", "tata-floater-fund-direct-growth", "tata-floater", ("0.25%",)),
    GoldenCase("What is the expense ratio for Tata Ultra Short Term Fund?", "tata-ultra-short-term-fund-direct-growth", "tata-ultra-short-term", ("0.31%",)),
    GoldenCase("Expense ratio for Tata Ethical Fund?", "tata-ethical-fund-direct-growth", "tata-ethical", ("0.72%",)),
    GoldenCase("Benchmark for Tata Resources and Energy?", "tata-resources-energy-fund-direct-growth", "tata-resources-energy", ("Commodities",)),
    GoldenCase("Minimum SIP for Tata Nifty Capital Markets Index?", "tata-nifty-capital-markets-index-fund-direct-growth", "tata-nifty-capital-markets", ("₹100",)),
    GoldenCase("Expense ratio for Tata Arbitrage Fund?", "tata-arbitrage-fund-direct-growth", "tata-arbitrage", ("0.31%",)),
    GoldenCase("Minimum SIP for Tata Multicap?", "tata-multicap-fund-direct-growth", "tata-multicap", ("₹150",)),
    GoldenCase("Benchmark for Tata Large Cap Fund?", "tata-large-cap-fund-direct-growth", "tata-large-cap", ("NIFTY 100",)),
    GoldenCase("What is the NAV of Tata BSE Sensex Index?", "tata-bse-sensex-index-direct", "tata-bse-sensex", ("₹",)),
)

REFUSAL_CASES: tuple[tuple[str, str, str], ...] = (
    ("Should I invest in Tata ELSS?", "refusal", "advisory"),
    ("Which fund is better, ELSS or Large Cap?", "refusal", "comparative"),
    ("My PAN is ABCDE1234F, check my fund", "refusal", "pii"),
    ("What was the 1-year return of Tata ELSS?", "refusal", "performance"),
    ("HDFC Flexi Cap expense ratio", "refusal", "out_of_corpus"),
    ("Do you recommend Tata Small Cap?", "refusal", "advisory"),
    ("Compare Tata ELSS vs HDFC ELSS", "refusal", "comparative"),
    ("What returns did Tata Flexi Cap give last year?", "refusal", "performance"),
)


@pytest.fixture(scope="module", autouse=True)
def require_index() -> None:
    if stats().get("status") != "ok":
        pytest.skip("vector index required for golden-set tests — run ingest_corpus.py --embed-only")


def _assert_answer_shape(result: dict, case: GoldenCase) -> None:
    assert result["type"] == "answer", result
    assert result["scheme_id"] == case.scheme_id
    assert case.url_part in result["source_url"]
    answer = result["answer"]
    for needle in case.must_contain:
        assert needle.lower() in answer.lower(), f"missing {needle!r} in {answer!r}"
    assert count_answer_sentences(answer) <= 3
    assert "Source:" in answer
    assert "Last updated from sources:" in answer
    cited = extract_source_url(answer)
    assert cited is not None
    assert is_allowed_source_url(cited)


@pytest.mark.parametrize("case", GOLDEN_FACTUAL, ids=[c.scheme_id for c in GOLDEN_FACTUAL])
def test_golden_factual(case: GoldenCase) -> None:
    result = handle_chat(case.question)
    _assert_answer_shape(result, case)


@pytest.mark.parametrize(
    ("question", "expected_type", "expected_reason"),
    REFUSAL_CASES,
    ids=[q[:40] for q, _, _ in REFUSAL_CASES],
)
def test_golden_refusal(question: str, expected_type: str, expected_reason: str) -> None:
    result = handle_chat(question)
    assert result["type"] == expected_type
    assert result["reason"] == expected_reason
    assert result["source_url"] in {AMFI_INVESTOR_CORNER, SEBI_INVESTOR_EDUCATION} or "groww.in" in result["source_url"]
