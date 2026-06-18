"""Build or refresh the BGE-large vector index from processed chunks."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ingestion.embed_index import index_scheme, rebuild_index, search, stats

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embed chunks with BGE-large and upsert into data/index/.",
    )
    parser.add_argument("scheme_id", nargs="?", help="Index one scheme (omit with --all)")
    parser.add_argument("--all", action="store_true", help="Rebuild full index from all *_chunks.json")
    parser.add_argument("--stats", action="store_true", help="Print index stats and exit")
    parser.add_argument("--query", help="Test similarity search query")
    parser.add_argument("--scheme", help="Optional scheme_id filter for --query")
    parser.add_argument("-k", type=int, default=3, help="Top-k for --query (default: 3)")
    args = parser.parse_args()

    if args.stats:
        print(json.dumps(stats(), indent=2))
        return

    if args.query:
        hits = search(args.query, scheme_id=args.scheme, k=args.k)
        if not hits:
            logger.info("No results (index may be empty).")
            return
        for hit in hits:
            meta = hit["metadata"]
            logger.info(
                "[%s] %s | distance=%.4f | %s",
                meta.get("section"),
                meta.get("scheme_id"),
                hit["distance"],
                hit["content"][:100],
            )
        return

    if args.all:
        result = rebuild_index()
        logger.info("Rebuilt index: %s", json.dumps(result, indent=2))
        return

    if not args.scheme_id:
        parser.error("Provide scheme_id, or use --all, --stats, or --query")

    result = index_scheme(args.scheme_id)
    logger.info("Indexed scheme: %s", json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
