"""Scheduler and corpus freshness tests (Phase 5)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.corpus_freshness import corpus_freshness
from app.core.corpus_registry import load_corpus_registry
from config.settings import get_settings


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "daily-ingest.yml"


def test_corpus_registry_has_fifteen_schemes() -> None:
    schemes = load_corpus_registry()
    assert len(schemes) == 15
    assert all(s.last_ingested_at for s in schemes)


def test_daily_ingest_workflow_exists() -> None:
    assert WORKFLOW.is_file()
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "30 4 * * *" in text  # 10:00 IST
    assert "ingest_corpus.py" in text
    assert "chroma-index" in text


def test_corpus_freshness_fresh_when_recent() -> None:
    payload = corpus_freshness()
    assert payload["scheme_count"] == 15
    assert payload["status"] in {"fresh", "stale", "unknown"}
    if payload["status"] == "fresh":
        assert payload["age_hours"] <= get_settings().corpus_stale_hours


def test_corpus_freshness_stale_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    old = datetime.now(timezone.utc) - timedelta(hours=48)
    schemes = load_corpus_registry()

    class FakeScheme:
        def __init__(self, ts: str) -> None:
            self.last_ingested_at = ts

    monkeypatch.setattr(
        "app.core.corpus_freshness.load_corpus_registry",
        lambda: [FakeScheme(old.isoformat()) for _ in schemes],
    )
    payload = corpus_freshness()
    assert payload["status"] == "stale"
    assert payload["age_hours"] > 26
