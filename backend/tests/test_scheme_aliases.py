"""Tests for scheme alias resolution (Phase 2)."""

from app.core.scheme_aliases import resolve_scheme, scheme_needs_clarification


def test_resolve_elss_alias() -> None:
    scheme = resolve_scheme("What is the minimum SIP for Tata ELSS?")
    assert scheme is not None
    assert scheme.scheme_id == "tata-elss-fund-direct-growth"


def test_resolve_full_scheme_name() -> None:
    scheme = resolve_scheme("expense ratio for Tata Large Cap Fund Direct Growth")
    assert scheme is not None
    assert scheme.scheme_id == "tata-large-cap-fund-direct-growth"


def test_clarification_when_scheme_missing() -> None:
    assert scheme_needs_clarification("What is the expense ratio?", None) is True


def test_no_clarification_when_scheme_resolved() -> None:
    scheme = resolve_scheme("minimum SIP for Tata ELSS Fund Direct Growth")
    assert scheme is not None
    assert scheme_needs_clarification("minimum SIP", scheme) is False


def test_resolve_arbitage_typo() -> None:
    scheme = resolve_scheme("expense ratio for Tata Arbitage Fund")
    assert scheme is not None
    assert scheme.scheme_id == "tata-arbitrage-fund-direct-growth"
