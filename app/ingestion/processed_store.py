"""Persist parsed scheme documents under data/processed/ for manual review."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.ingestion.parser import ParsedSchemeDocument
from config.settings import Settings, get_settings


def processed_path_for(scheme_id: str, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.processed_dir / f"{scheme_id}.json"


def parsed_document_to_dict(
    parsed: ParsedSchemeDocument,
    *,
    parsed_at: datetime | None = None,
) -> dict[str, Any]:
    return {
        "scheme_id": parsed.scheme_id,
        "scheme_name": parsed.scheme_name,
        "source_url": parsed.source_url,
        "parsed_at": (parsed_at or datetime.now(timezone.utc)).isoformat(),
        "structured_fields": parsed.structured_fields,
        "sections": parsed.sections,
    }


def save_processed_document(
    parsed: ParsedSchemeDocument,
    *,
    settings: Settings | None = None,
    path: Path | None = None,
) -> Path:
    """Write parsed scheme JSON to data/processed/<scheme_id>.json."""
    settings = settings or get_settings()
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    out_path = path or processed_path_for(parsed.scheme_id, settings)
    payload = parsed_document_to_dict(parsed)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def load_processed_document(
    scheme_id: str,
    *,
    settings: Settings | None = None,
    path: Path | None = None,
) -> dict[str, Any] | None:
    """Load a previously saved processed JSON file, if present."""
    settings = settings or get_settings()
    file_path = path or processed_path_for(scheme_id, settings)
    if not file_path.is_file():
        return None
    return json.loads(file_path.read_text(encoding="utf-8"))


def update_schemes_metadata(
    parsed: ParsedSchemeDocument,
    *,
    settings: Settings | None = None,
    last_ingested_at: datetime | None = None,
) -> Path:
    """
    Merge structured fields into data/processed/schemes.json
    (aggregate metadata for all schemes).
    """
    settings = settings or get_settings()
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    meta_path = settings.schemes_metadata_path

    if meta_path.is_file():
        aggregate: dict[str, Any] = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        aggregate = {"amc": "Tata Mutual Fund", "schemes": {}}

    schemes = aggregate.setdefault("schemes", {})
    schemes[parsed.scheme_id] = {
        "scheme_name": parsed.scheme_name,
        "source_url": parsed.source_url,
        "last_ingested_at": (last_ingested_at or datetime.now(timezone.utc)).isoformat(),
        **parsed.structured_fields,
    }

    meta_path.write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return meta_path


def reset_schemes_metadata(settings: Settings | None = None) -> Path:
    """Clear aggregate metadata before a full corpus re-process."""
    settings = settings or get_settings()
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    meta_path = settings.schemes_metadata_path
    payload = {"amc": "Tata Mutual Fund", "schemes": {}}
    meta_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta_path
