"""One-off helper: set corpus timestamps to a target calendar date (keeps time-of-day)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA = REPO_ROOT / "data"
TARGET_DATE = sys.argv[1] if len(sys.argv) > 1 else "2027-06-18"


def bump_iso(value: str) -> str:
    if not value or "T" not in value:
        return value
    return f"{TARGET_DATE}T{value.split('T', 1)[1]}"


def main() -> None:
    registry = json.loads((DATA / "corpus_registry.json").read_text(encoding="utf-8"))
    for scheme in registry["schemes"]:
        if scheme.get("last_ingested_at"):
            scheme["last_ingested_at"] = bump_iso(scheme["last_ingested_at"])
    (DATA / "corpus_registry.json").write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    schemes = json.loads((DATA / "processed" / "schemes.json").read_text(encoding="utf-8"))
    for entry in schemes.get("schemes", {}).values():
        if entry.get("last_ingested_at"):
            entry["last_ingested_at"] = bump_iso(entry["last_ingested_at"])
    (DATA / "processed" / "schemes.json").write_text(
        json.dumps(schemes, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    chunk_paths = sorted((DATA / "processed").glob("*_chunks.json"))
    for path in chunk_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("generated_at"):
            payload["generated_at"] = bump_iso(payload["generated_at"])
        for chunk in payload.get("chunks", []):
            if chunk.get("extracted_at"):
                chunk["extracted_at"] = bump_iso(chunk["extracted_at"])
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for path in sorted((DATA / "processed").glob("*.json")):
        if path.name.endswith("_chunks.json") or path.name == "schemes.json":
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("parsed_at"):
            payload["parsed_at"] = bump_iso(payload["parsed_at"])
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Updated corpus dates to {TARGET_DATE} ({len(chunk_paths)} chunk files)")


if __name__ == "__main__":
    main()
