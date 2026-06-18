"""Load and validate the corpus registry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import get_settings

REQUIRED_SCHEME_FIELDS = (
    "amc",
    "scheme_id",
    "scheme_name",
    "source_url",
    "category",
    "last_ingested_at",
)


@dataclass(frozen=True)
class SchemeEntry:
    amc: str
    scheme_id: str
    scheme_name: str
    source_url: str
    category: str
    last_ingested_at: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SchemeEntry:
        missing = [field for field in REQUIRED_SCHEME_FIELDS if field not in data]
        if missing:
            raise ValueError(f"Scheme entry missing fields: {missing}")
        return cls(
            amc=data["amc"],
            scheme_id=data["scheme_id"],
            scheme_name=data["scheme_name"],
            source_url=data["source_url"],
            category=data["category"],
            last_ingested_at=data["last_ingested_at"],
        )


def load_corpus_registry(path: Path | None = None) -> list[SchemeEntry]:
    """Load all scheme entries from the corpus registry JSON file."""
    registry_path = path or get_settings().corpus_registry_path
    with registry_path.open(encoding="utf-8") as f:
        payload = json.load(f)

    schemes = payload.get("schemes")
    if not isinstance(schemes, list):
        raise ValueError("corpus_registry.json must contain a 'schemes' array")

    return [SchemeEntry.from_dict(entry) for entry in schemes]


def get_scheme_by_id(scheme_id: str, path: Path | None = None) -> SchemeEntry | None:
    """Return a single scheme entry by scheme_id, or None if not found."""
    for scheme in load_corpus_registry(path):
        if scheme.scheme_id == scheme_id:
            return scheme
    return None


def update_last_ingested_at(
    scheme_id: str,
    ingested_at: datetime,
    path: Path | None = None,
) -> None:
    """Update last_ingested_at for one scheme in corpus_registry.json."""
    registry_path = path or get_settings().corpus_registry_path
    with registry_path.open(encoding="utf-8") as f:
        payload = json.load(f)

    iso = ingested_at.isoformat() if isinstance(ingested_at, datetime) else ingested_at
    for entry in payload.get("schemes", []):
        if entry.get("scheme_id") == scheme_id:
            entry["last_ingested_at"] = iso
            break
    else:
        raise ValueError(f"scheme_id not in registry: {scheme_id}")

    with registry_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
