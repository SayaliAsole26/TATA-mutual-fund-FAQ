"""Preview fetch + parse and write data/raw + data/processed for manual verification."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.corpus_registry import (
    SchemeEntry,
    load_corpus_registry,
    update_last_ingested_at,
)
from app.ingestion.fetcher import fetch_scheme
from app.ingestion.parser import parse_scheme_content
from app.ingestion.chunker import chunk_and_save_scheme
from app.ingestion.embed_index import index_scheme, rebuild_index
from app.ingestion.processed_store import (
    reset_schemes_metadata,
    save_processed_document,
    update_schemes_metadata,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def process_scheme(scheme: SchemeEntry, *, force_live: bool = False) -> list[str]:
    fetched = fetch_scheme(scheme, force_live=force_live)
    parsed = parse_scheme_content(fetched, scheme_name=scheme.scheme_name)

    raw_note = "snapshot" if fetched.from_snapshot else "live fetch"
    processed_path = save_processed_document(parsed)
    chunks, chunks_path = chunk_and_save_scheme(scheme.scheme_id)
    index_result = index_scheme(scheme.scheme_id)
    meta_path = update_schemes_metadata(parsed, last_ingested_at=fetched.fetched_at)
    update_last_ingested_at(scheme.scheme_id, fetched.fetched_at)

    logger.info("Scheme: %s", scheme.scheme_name)
    logger.info(
        "Raw (%s): data/raw/%s.html + data/raw/%s.json + data/raw/%s.cleaned.txt",
        raw_note,
        scheme.scheme_id,
        scheme.scheme_id,
        scheme.scheme_id,
    )
    logger.info("Processed: %s", processed_path)
    logger.info("Chunks: %s (%d sections)", chunks_path, len(chunks))
    logger.info("Indexed: %d vectors in %s", index_result["chunk_count"], index_result["index_dir"])
    logger.info("Metadata aggregate: %s", meta_path)
    logger.info("Fields extracted: %s", ", ".join(parsed.structured_fields.keys()))
    return list(parsed.structured_fields.keys())


def process_all(*, force_live: bool = False) -> None:
    schemes = load_corpus_registry()
    reset_schemes_metadata()
    logger.info("Processing %d schemes from corpus registry", len(schemes))

    failed: list[str] = []
    for index, scheme in enumerate(schemes, start=1):
        logger.info("--- [%d/%d] %s ---", index, len(schemes), scheme.scheme_id)
        try:
            process_scheme(scheme, force_live=force_live)
        except Exception as exc:
            logger.error("Failed %s: %s", scheme.scheme_id, exc)
            failed.append(scheme.scheme_id)

    if failed:
        raise SystemExit(f"Completed with failures ({len(failed)}): {', '.join(failed)}")

    # Full atomic rebuild ensures a consistent index after batch ingest
    rebuild_result = rebuild_index()
    logger.info(
        "Index rebuilt: %d chunks across %d schemes -> %s",
        rebuild_result["chunk_count"],
        rebuild_result["scheme_count"],
        rebuild_result["index_dir"],
    )
    logger.info("All %d schemes processed successfully", len(schemes))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch, parse, and write data/raw + data/processed.",
    )
    parser.add_argument(
        "scheme_id",
        nargs="?",
        help="e.g. tata-elss-fund-direct-growth (omit with --all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all 15 schemes in corpus_registry.json",
    )
    parser.add_argument(
        "--force-live",
        action="store_true",
        help="Fetch live from Groww instead of using an existing raw snapshot",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all scheme_ids and exit",
    )
    args = parser.parse_args()

    if args.list:
        for scheme in load_corpus_registry():
            print(scheme.scheme_id)
        return

    if args.all:
        process_all(force_live=args.force_live)
        return

    if not args.scheme_id:
        parser.error("Provide scheme_id or use --all")

    from app.core.corpus_registry import get_scheme_by_id

    scheme = get_scheme_by_id(args.scheme_id)
    if scheme is None:
        raise SystemExit(f"Unknown scheme_id: {args.scheme_id}")
    process_scheme(scheme, force_live=args.force_live)


if __name__ == "__main__":
    main()
