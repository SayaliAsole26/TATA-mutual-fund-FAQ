"""Export human-readable ChromaDB manifest to data/index/chromadb/."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ingestion.embed_index import export_index_manifest, stats

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Chroma index to readable JSON under data/index/chromadb/.",
    )
    parser.add_argument(
        "--full-vectors",
        action="store_true",
        help="Include all 1024 embedding dimensions in JSON (large file)",
    )
    parser.add_argument(
        "--preview-dims",
        type=int,
        default=8,
        help="Number of embedding dimensions in preview (default: 8)",
    )
    args = parser.parse_args()

    index_stats = stats()
    if index_stats.get("status") != "ok":
        raise SystemExit(
            f"Index not ready (status={index_stats.get('status')}). "
            "Run: python scripts/preview_embed.py --all"
        )

    path = export_index_manifest(
        preview_dims=args.preview_dims,
        include_full_vectors=args.full_vectors,
    )
    logger.info("Manifest: %s", path)
    logger.info("Per-scheme files: %s", path.parent / "by_scheme")
    print(json.dumps({"manifest": str(path), **index_stats}, indent=2))


if __name__ == "__main__":
    main()
