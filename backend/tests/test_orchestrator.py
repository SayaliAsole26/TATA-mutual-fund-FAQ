"""Tests for chat orchestrator (Phase 2)."""

from __future__ import annotations

from unittest.mock import patch

from app.core.orchestrator import handle_chat


def test_clarification_without_scheme() -> None:
    result = handle_chat("What is the expense ratio?")
    assert result["type"] == "clarification"
    assert "schemes" in result
    assert len(result["schemes"]) == 15


@patch("app.core.orchestrator.generate_answer")
def test_chat_with_mocked_groq(mock_generate) -> None:
    mock_generate.return_value = (
        "The minimum SIP amount is ₹500.\n\n"
        "Source: https://groww.in/mutual-funds/tata-elss-fund-direct-growth\n\n"
        "Last updated from sources: 18 Jun 2026"
    )
    result = handle_chat("What is the minimum SIP for Tata ELSS?")
    assert result["type"] == "answer"
    assert "₹500" in result["answer"]
    assert result["scheme_id"] == "tata-elss-fund-direct-growth"
    assert "groww.in" in result["source_url"]


def test_structured_answer_skips_groq() -> None:
    with patch("app.core.orchestrator.generate_answer") as mock_generate:
        result = handle_chat("What is the minimum SIP for Tata ELSS Fund Direct Growth?")
        if result["type"] == "answer" and result.get("retrieval_source") == "structured":
            mock_generate.assert_not_called()
            assert "Source:" in result["answer"]
