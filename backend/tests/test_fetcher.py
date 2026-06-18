"""Tests for ingestion fetcher (Phase 1.1.3)."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from app.core.corpus_registry import SchemeEntry
from app.ingestion.fetcher import (
    FetchedContent,
    RateLimiter,
    fetch_live,
    fetch_scheme,
    html_to_text,
    load_snapshot,
    raw_html_path_for,
    raw_json_path_for,
    save_snapshot,
)
from config.settings import Settings, get_settings


@pytest.fixture
def scheme() -> SchemeEntry:
    return SchemeEntry(
        amc="Tata Mutual Fund",
        scheme_id="tata-elss-fund-direct-growth",
        scheme_name="Tata ELSS Fund Direct Growth",
        source_url="https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        category="ELSS",
        last_ingested_at=None,
    )


@pytest.fixture
def fixture_html(fixture_text: str) -> str:
    return f"<html><body><pre>{fixture_text}</pre></body></html>"


@pytest.fixture
def fixture_text() -> str:
    path = Path(__file__).parent / "fixtures" / "tata-elss-fund-direct-growth.md"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    s = get_settings()
    s.raw_dir.mkdir(parents=True, exist_ok=True)
    yield s
    get_settings.cache_clear()


def test_load_snapshot_missing(settings: Settings, scheme: SchemeEntry) -> None:
    assert load_snapshot(scheme.scheme_id, settings=settings) is None


def test_save_and_load_snapshot(
    settings: Settings,
    scheme: SchemeEntry,
    fixture_text: str,
    fixture_html: str,
) -> None:
    fetched = FetchedContent(
        scheme_id=scheme.scheme_id,
        source_url=scheme.source_url,
        content=fixture_text,
        fetched_at=datetime.now(timezone.utc),
        from_snapshot=False,
        raw_html=fixture_html,
    )
    json_path = save_snapshot(fetched, settings=settings, scheme_name=scheme.scheme_name)
    assert json_path.is_file()
    assert raw_html_path_for(scheme.scheme_id, settings).is_file()
    from app.ingestion.fetcher import raw_cleaned_path_for

    assert raw_cleaned_path_for(scheme.scheme_id, settings).is_file()

    loaded = load_snapshot(scheme.scheme_id, settings=settings, scheme_name=scheme.scheme_name)
    assert loaded is not None
    assert loaded.from_snapshot is True
    assert loaded.source_url == scheme.source_url
    assert "Expense ratio" in loaded.content


def test_fetch_scheme_prefers_snapshot(
    settings: Settings,
    scheme: SchemeEntry,
    fixture_html: str,
) -> None:
    save_snapshot(
        FetchedContent(
            scheme_id=scheme.scheme_id,
            source_url=scheme.source_url,
            content="placeholder",
            fetched_at=datetime.now(timezone.utc),
            from_snapshot=False,
            raw_html=fixture_html,
        ),
        settings=settings,
        scheme_name=scheme.scheme_name,
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.ingestion.fetcher.fetch_live", MagicMock())
        result = fetch_scheme(scheme, settings=settings)
        assert result.from_snapshot is True


def test_fetch_scheme_force_live(
    settings: Settings,
    scheme: SchemeEntry,
    fixture_html: str,
) -> None:
    save_snapshot(
        FetchedContent(
            scheme_id=scheme.scheme_id,
            source_url=scheme.source_url,
            content="placeholder",
            fetched_at=datetime.now(timezone.utc),
            from_snapshot=False,
            raw_html=fixture_html,
        ),
        settings=settings,
        scheme_name=scheme.scheme_name,
    )

    live = FetchedContent(
        scheme_id=scheme.scheme_id,
        source_url=scheme.source_url,
        content="live content",
        fetched_at=datetime.now(timezone.utc),
        from_snapshot=False,
        raw_html="<html><body>live</body></html>",
    )
    mock_live = MagicMock(return_value=live)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.ingestion.fetcher.fetch_live", mock_live)
        result = fetch_scheme(scheme, settings=settings, force_live=True, save_after_live_fetch=False)
        mock_live.assert_called_once()

    assert result.content == "live content"
    assert result.from_snapshot is False


def test_rate_limiter_waits() -> None:
    limiter = RateLimiter(delay_seconds=0.05)
    limiter.wait()
    limiter.wait()


def test_html_to_text_strips_scripts() -> None:
    html = "<html><script>bad()</script><body><p>Expense ratio</p><p>1.17%</p></body></html>"
    text = html_to_text(html)
    assert "bad()" not in text
    assert "Expense ratio" in text


def test_fetch_live_uses_rate_limiter(scheme: SchemeEntry, settings: Settings) -> None:
    limiter = MagicMock()
    limiter.wait = MagicMock()

    response = httpx.Response(
        200,
        text="<html><body><h1>Tata ELSS Fund Direct Growth</h1></body></html>",
        request=httpx.Request("GET", scheme.source_url),
    )
    client = MagicMock()
    client.get.return_value = response

    fetched = fetch_live(scheme, settings=settings, rate_limiter=limiter, client=client)
    limiter.wait.assert_called_once()
    client.get.assert_called_once_with(scheme.source_url)
    assert scheme.source_url in fetched.content
    assert fetched.raw_html is not None
