"""POST /api/ingest — admin-only manual re-index (Phase 3 optional)."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException

from app.api.schemas import IngestResponse
from config.settings import BACKEND_ROOT, get_settings

router = APIRouter()
logger = logging.getLogger(__name__)

INGEST_SCRIPT = BACKEND_ROOT / "scripts" / "ingest_corpus.py"


@router.post("/ingest", response_model=IngestResponse)
def post_ingest(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> IngestResponse:
    settings = get_settings()
    if not settings.ingest_api_key:
        raise HTTPException(status_code=503, detail="Ingest API is not configured")
    if not x_admin_key or x_admin_key != settings.ingest_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin key")

    if not INGEST_SCRIPT.is_file():
        raise HTTPException(status_code=500, detail="Ingestion script not found")

    logger.info("Manual ingest triggered via API")
    completed = subprocess.run(
        [sys.executable, str(INGEST_SCRIPT)],
        cwd=str(BACKEND_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        logger.error("Manual ingest failed: %s", completed.stderr[-500:])
        raise HTTPException(status_code=500, detail="Ingestion failed")

    return IngestResponse(status="ok", message="Corpus ingestion completed")
