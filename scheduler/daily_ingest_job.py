"""Daily ingestion job — runs full corpus pipeline at 10:00 IST."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INGEST_SCRIPT = ROOT / "scripts" / "ingest_corpus.py"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    if not INGEST_SCRIPT.is_file():
        raise SystemExit(f"Missing ingestion script: {INGEST_SCRIPT}")

    logger.info("Starting daily corpus ingest: %s", INGEST_SCRIPT)
    completed = subprocess.run(
        [sys.executable, str(INGEST_SCRIPT)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    logger.info("Daily corpus ingest completed successfully")


if __name__ == "__main__":
    main()
