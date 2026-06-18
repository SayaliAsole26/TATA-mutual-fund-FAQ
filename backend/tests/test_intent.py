"""Tests for intent → section mapping (Phase 2)."""

from app.core.intent import detect_intent_section, is_nav_query


def test_detect_expense_ratio() -> None:
    assert detect_intent_section("What is the annual fee?") == "expense_ratio"


def test_detect_min_sip() -> None:
    assert detect_intent_section("minimum SIP amount") == "min_sip"


def test_detect_fund_managers() -> None:
    assert detect_intent_section("Who manages this fund?") == "fund_managers"


def test_nav_query_detection() -> None:
    assert is_nav_query("What is the latest NAV?") is True
    assert is_nav_query("minimum SIP") is False
