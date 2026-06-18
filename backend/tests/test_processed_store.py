"""Tests for data/processed/ storage."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.ingestion.parser import ParsedSchemeDocument, parse_scheme_content
from app.ingestion.processed_store import (
    load_processed_document,
    save_processed_document,
    update_schemes_metadata,
)
from app.ingestion.fetcher import FetchedContent
from config.settings import get_settings


@pytest.fixture
def settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    s = get_settings()
    s.raw_dir.mkdir(parents=True, exist_ok=True)
    s.processed_dir.mkdir(parents=True, exist_ok=True)
    s.index_dir.mkdir(parents=True, exist_ok=True)
    yield s
    get_settings.cache_clear()


@pytest.fixture
def parsed() -> ParsedSchemeDocument:
    fixture = Path(__file__).parent / "fixtures" / "tata-elss-fund-direct-growth.md"
    fetched = FetchedContent(
        scheme_id="tata-elss-fund-direct-growth",
        source_url="https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        content=fixture.read_text(encoding="utf-8"),
        fetched_at=datetime.now(timezone.utc),
        from_snapshot=True,
    )
    return parse_scheme_content(fetched)


def test_save_and_load_processed(settings, parsed: ParsedSchemeDocument) -> None:
    path = save_processed_document(parsed, settings=settings)
    assert path.parent == settings.processed_dir
    assert path.name == "tata-elss-fund-direct-growth.json"

    loaded = load_processed_document(parsed.scheme_id, settings=settings)
    assert loaded is not None
    assert loaded["structured_fields"]["expense_ratio"] == "1.17%"
    assert "sections" in loaded


def test_update_schemes_metadata(settings, parsed: ParsedSchemeDocument) -> None:
    save_processed_document(parsed, settings=settings)
    meta_path = update_schemes_metadata(parsed, settings=settings)
    assert meta_path == settings.processed_dir / "schemes.json"
    assert meta_path.is_file()

    import json

    data = json.loads(meta_path.read_text(encoding="utf-8"))
    assert "tata-elss-fund-direct-growth" in data["schemes"]
    assert data["schemes"]["tata-elss-fund-direct-growth"]["min_sip"] == "₹500"


def test_data_layout_dirs(settings) -> None:
    assert settings.raw_dir.name == "raw"
    assert settings.processed_dir.name == "processed"
    assert settings.index_dir.name == "index"
    assert settings.vector_store_dir == settings.index_dir
