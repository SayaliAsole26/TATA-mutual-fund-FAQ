"""Full corpus ingestion: fetch → parse → chunk → embed → export manifest."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.corpus_registry import SchemeEntry, load_corpus_registry, update_last_ingested_at
from app.ingestion.chunker import chunk_and_save_scheme
from app.ingestion.embed_index import export_index_manifest, rebuild_index, stats
from app.ingestion.fetcher import fetch_scheme
from app.ingestion.parser import parse_scheme_content
from app.ingestion.processed_store import (
    reset_schemes_metadata,
    save_processed_document,
    update_schemes_metadata,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def ingest_scheme(scheme: SchemeEntry, *, force_live: bool = False) -> None:
    """Fetch, parse, and chunk one scheme (embed runs after full batch)."""
    fetched = fetch_scheme(scheme, force_live=force_live)
    parsed = parse_scheme_content(fetched, scheme_name=scheme.scheme_name)

    save_processed_document(parsed)
    chunks, chunks_path = chunk_and_save_scheme(scheme.scheme_id)
    update_schemes_metadata(parsed, last_ingested_at=fetched.fetched_at)
    update_last_ingested_at(scheme.scheme_id, fetched.fetched_at)

    logger.info(
        "%s: %d chunks -> %s",
        scheme.scheme_name,
        len(chunks),
        chunks_path.name,
    )


def ingest_corpus(*, force_live: bool = False, skip_embed: bool = False) -> dict:
    """Run the full Phase 1 pipeline for all 15 schemes."""
    started = time.monotonic()
    schemes = load_corpus_registry()
    reset_schemes_metadata()

    failed: list[SchemeEntry] = []
    for index, scheme in enumerate(schemes, start=1):
        logger.info("--- [%d/%d] %s ---", index, len(schemes), scheme.scheme_id)
        try:
            ingest_scheme(scheme, force_live=force_live)
        except Exception as exc:
            logger.error("Failed %s: %s", scheme.scheme_id, exc)
            failed.append(scheme)

    if failed:
        logger.info("Retrying %d failed scheme(s) once", len(failed))
        retry_failed: list[SchemeEntry] = []
        for scheme in failed:
            try:
                ingest_scheme(scheme, force_live=force_live)
            except Exception as exc:
                logger.error("Retry failed %s: %s", scheme.scheme_id, exc)
                retry_failed.append(scheme)
        failed = retry_failed

    result: dict = {
        "schemes_total": len(schemes),
        "schemes_failed": [s.scheme_id for s in failed],
        "duration_seconds": round(time.monotonic() - started, 1),
    }

    if failed:
        result["status"] = "partial_failure"
        logger.error("Ingestion completed with failures: %s", result["schemes_failed"])
    else:
        result["status"] = "ok"
        logger.info("All %d schemes fetched, parsed, and chunked", len(schemes))

    if not skip_embed and not failed:
        logger.info("Rebuilding BGE-large vector index...")
        embed_result = rebuild_index()
        result["index"] = embed_result
        manifest_path = export_index_manifest()
        result["manifest"] = str(manifest_path)
        result["index_stats"] = stats()
    elif skip_embed:
        logger.info("Skipping embed (--skip-embed)")
    else:
        logger.warning("Skipping embed due to scheme failures")

    result["duration_seconds"] = round(time.monotonic() - started, 1)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Full corpus ingestion pipeline (Phase 1).")
    parser.add_argument(
        "--force-live",
        action="store_true",
        help="Fetch live from Groww instead of local raw snapshots",
    )
    parser.add_argument(
        "--skip-embed",
        action="store_true",
        help="Only fetch/parse/chunk; do not rebuild vector index",
    )
    args = parser.parse_args()

    result = ingest_corpus(force_live=args.force_live, skip_embed=args.skip_embed)
    print(json.dumps(result, indent=2))

    if result.get("status") != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
