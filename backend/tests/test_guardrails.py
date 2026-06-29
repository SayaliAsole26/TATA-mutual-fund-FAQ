"""Tests for Phase 3 guardrails and refusal templates."""

from __future__ import annotations

from unittest.mock import patch

from app.core.formatter import (
    build_formatted_answer,
    count_answer_sentences,
    is_allowed_citation_url,
    truncate_answer_body,
)
from app.core.guardrails import (
    classify_input,
    contains_pii,
    is_advisory_query,
    is_comparative_query,
    is_out_of_corpus_query,
    is_performance_query,
    repair_output,
    validate_output,
)
from app.core.orchestrator import handle_chat
from app.core.templates import (
    AMFI_INVESTOR_CORNER,
    SEBI_INVESTOR_EDUCATION,
    refusal_response,
)


# --- Input guardrails ---


def test_pii_pan_detected() -> None:
    assert contains_pii("My PAN is ABCDE1234F, check my ELSS")
    result = classify_input("My PAN is ABCDE1234F, check my fund")
    assert result.blocked is True
    assert result.reason == "pii"


def test_pii_email_detected() -> None:
    assert contains_pii("Contact user@example.com about ELSS")


def test_advisory_should_i_invest() -> None:
    assert is_advisory_query("Should I invest in Tata Small Cap?")
    result = classify_input("Should I invest in this fund?")
    assert result.reason == "advisory"


def test_comparative_which_fund_better() -> None:
    assert is_comparative_query("Which fund is better, ELSS or Large Cap?")
    result = classify_input("Which fund is better, ELSS or Large Cap?")
    assert result.reason == "comparative"


def test_performance_one_year_return() -> None:
    assert is_performance_query("What was the 1-year return?")
    result = classify_input("What was the 1-year return?")
    assert result.reason == "performance"


def test_out_of_corpus_hdfc() -> None:
    assert is_out_of_corpus_query("HDFC Flexi Cap expense ratio")
    result = classify_input("HDFC Flexi Cap expense ratio")
    assert result.reason == "out_of_corpus"


def test_tata_query_not_out_of_corpus() -> None:
    assert is_out_of_corpus_query("Tata ELSS expense ratio") is False


# --- Refusal templates ---


def test_advisory_refusal_has_educational_link() -> None:
    payload = refusal_response("advisory")
    assert payload["type"] == "refusal"
    assert payload["reason"] == "advisory"
    assert AMFI_INVESTOR_CORNER in payload["answer"]
    assert payload["source_url"] == AMFI_INVESTOR_CORNER


def test_comparative_refusal_has_sebi_link() -> None:
    payload = refusal_response("comparative")
    assert SEBI_INVESTOR_EDUCATION in payload["answer"]


def test_performance_refusal_with_scheme() -> None:
    payload = refusal_response(
        "performance",
        scheme_name="Tata ELSS Fund Direct Growth",
        scheme_url="https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
    )
    assert "groww.in/mutual-funds/tata-elss-fund-direct-growth" in payload["answer"]
    assert "cannot calculate" in payload["answer"].lower()


# --- Output validation ---


def test_validate_output_accepts_good_answer() -> None:
    answer = build_formatted_answer(
        "The minimum SIP amount is ₹500.",
        "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        "2027-06-18T18:09:51+00:00",
    )
    result = validate_output(answer)
    assert result.valid is True


def test_validate_output_rejects_four_sentences() -> None:
    body = "One. Two. Three. Four."
    answer = build_formatted_answer(
        body,
        "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        "2027-06-18T18:09:51+00:00",
    )
    result = validate_output(answer)
    assert result.valid is False
    assert "too_many_sentences" in result.issues


def test_validate_output_rejects_bad_url() -> None:
    answer = (
        "The expense ratio is 1.17%.\n\n"
        "Source: https://evil.example.com\n\n"
        "Last updated from sources: 18 Jun 2027"
    )
    result = validate_output(answer)
    assert result.valid is False
    assert "disallowed_source_url" in result.issues


def test_validate_output_rejects_advice_language() -> None:
    answer = build_formatted_answer(
        "You should invest in this fund today.",
        "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        "2027-06-18T18:09:51+00:00",
    )
    result = validate_output(answer)
    assert "advice_language" in result.issues


def test_truncate_answer_body() -> None:
    text = "One. Two. Three. Four."
    assert truncate_answer_body(text, max_sentences=3) == "One. Two. Three."


def test_educational_urls_allowed() -> None:
    assert is_allowed_citation_url(AMFI_INVESTOR_CORNER)
    assert is_allowed_citation_url(SEBI_INVESTOR_EDUCATION)


def test_repair_output_truncates_sentences() -> None:
    long_body = "One. Two. Three. Four."
    broken = build_formatted_answer(
        long_body,
        "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        "2027-06-18T18:09:51+00:00",
    )
    fixed = repair_output(
        broken,
        fallback_url="https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        fallback_date="2027-06-18T18:09:51+00:00",
    )
    assert count_answer_sentences(fixed) <= 3
    assert validate_output(fixed).valid is True


# --- Orchestrator integration (refusal suite) ---


def test_orchestrator_advisory_refusal() -> None:
    result = handle_chat("Should I invest in Tata Small Cap?")
    assert result["type"] == "refusal"
    assert result["reason"] == "advisory"
    assert "amfiindia.com" in result["source_url"]


def test_orchestrator_comparative_refusal() -> None:
    result = handle_chat("Which fund is better, ELSS or Large Cap?")
    assert result["type"] == "refusal"
    assert result["reason"] == "comparative"


def test_orchestrator_pii_refusal() -> None:
    result = handle_chat("My PAN is ABCDE1234F, check my fund")
    assert result["type"] == "refusal"
    assert result["reason"] == "pii"


def test_orchestrator_performance_refusal() -> None:
    result = handle_chat("What returns did Tata ELSS give last year?")
    assert result["type"] == "refusal"
    assert result["reason"] == "performance"
    assert "groww.in" in result["source_url"]


@patch("app.core.orchestrator.generate_answer")
def test_orchestrator_validates_long_llm_output(mock_generate) -> None:
    mock_generate.return_value = (
        "Sentence one. Sentence two. Sentence three. Sentence four.\n\n"
        "Source: https://groww.in/mutual-funds/tata-flexi-cap-fund-direct-growth\n\n"
        "Last updated from sources: 18 Jun 2027"
    )
    result = handle_chat("Who manages Tata Flexi Cap Fund?")
    assert result["type"] == "answer"
    assert count_answer_sentences(result["answer"]) <= 3
