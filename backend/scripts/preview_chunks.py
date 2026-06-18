"""Generate data/processed/<scheme_id>_chunks.json for manual review."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.corpus_registry import get_scheme_by_id, load_corpus_registry
from app.ingestion.chunker import chunk_and_save_scheme, save_all_scheme_chunks

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build section chunks from processed + cleaned data.")
    parser.add_argument("scheme_id", nargs="?", help="Single scheme_id (omit with --all)")
    parser.add_argument("--all", action="store_true", help="Chunk all schemes with processed JSON")
    args = parser.parse_args()

    if args.all:
        paths = save_all_scheme_chunks()
        total = sum(json.loads(path.read_text(encoding="utf-8"))["chunk_count"] for path in paths.values())
        for scheme_id, path in sorted(paths.items()):
            count = json.loads(path.read_text(encoding="utf-8"))["chunk_count"]
            logger.info("%s: %d chunks -> %s", scheme_id, count, path)
        logger.info("Total: %d chunks across %d schemes", total, len(paths))
        return

    if not args.scheme_id:
        parser.error("Provide scheme_id or use --all")

    scheme = get_scheme_by_id(args.scheme_id)
    if scheme is None:
        raise SystemExit(f"Unknown scheme_id: {args.scheme_id}")

    chunks, path = chunk_and_save_scheme(args.scheme_id)
    logger.info("%s: %d chunks -> %s", scheme.scheme_name, len(chunks), path)
    for chunk in chunks:
        logger.info("  [%s] %s (%s)", chunk.section, chunk.content[:80], chunk.chunk_source)


if __name__ == "__main__":
    main()
