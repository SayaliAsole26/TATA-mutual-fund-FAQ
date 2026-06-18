"""Corpus freshness helpers for health monitoring (Phase 5)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.corpus_registry import load_corpus_registry
from config.settings import Settings, get_settings


def corpus_freshness(settings: Settings | None = None) -> dict:
    """Return staleness metadata for scheduled ingestion monitoring."""
    settings = settings or get_settings()
    schemes = load_corpus_registry()
    if not schemes:
        return {
            "status": "unknown",
            "scheme_count": 0,
            "stale_after_hours": settings.corpus_stale_hours,
        }

    timestamps: list[datetime] = []
    for scheme in schemes:
        raw = scheme.last_ingested_at
        if not raw:
            continue
        try:
            timestamps.append(datetime.fromisoformat(raw.replace("Z", "+00:00")))
        except ValueError:
            continue

    if not timestamps:
        return {
            "status": "unknown",
            "scheme_count": len(schemes),
            "stale_after_hours": settings.corpus_stale_hours,
        }

    newest = max(timestamps)
    age = datetime.now(timezone.utc) - newest.astimezone(timezone.utc)
    stale_limit = timedelta(hours=settings.corpus_stale_hours)
    is_stale = age > stale_limit

    return {
        "status": "stale" if is_stale else "fresh",
        "scheme_count": len(schemes),
        "newest_ingested_at": newest.isoformat(),
        "age_hours": round(age.total_seconds() / 3600, 1),
        "stale_after_hours": settings.corpus_stale_hours,
    }
