"""Rate limiting tests for /api/chat (Phase 5)."""

from __future__ import annotations

from app.middleware.rate_limit import ChatRateLimitMiddleware


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = ChatRateLimitMiddleware(app=None, requests_per_minute=2)  # type: ignore[arg-type]
    ip = "203.0.113.10"
    assert limiter._is_limited(ip) is False
    assert limiter._is_limited(ip) is False
    assert limiter._is_limited(ip) is True


def test_rate_limiter_disabled_when_zero() -> None:
    limiter = ChatRateLimitMiddleware(app=None, requests_per_minute=0)  # type: ignore[arg-type]
    assert limiter._is_limited("203.0.113.11") is False
    assert limiter._is_limited("203.0.113.11") is False
