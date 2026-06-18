"""Regenerate .cleaned.txt files from existing raw HTML for all corpus schemes."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.corpus_registry import load_corpus_registry
from app.ingestion.fetcher import regenerate_cleaned_txt

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    schemes = load_corpus_registry()
    written = 0
    for scheme in schemes:
        path = regenerate_cleaned_txt(scheme)
        if path is None:
            logger.warning("Skipped %s (no HTML snapshot)", scheme.scheme_id)
            continue
        logger.info("Wrote %s", path)
        written += 1
    logger.info("Regenerated %d/%d cleaned.txt files", written, len(schemes))


if __name__ == "__main__":
    main()
