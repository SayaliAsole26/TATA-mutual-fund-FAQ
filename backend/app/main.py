"""FastAPI application entrypoint (Phase 2c)."""

from __future__ import annotations

import logging
import subprocess
import sys
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, health, ingest, schemes
from app.ingestion.embed_index import stats
from config.settings import BACKEND_ROOT, get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_ingest_lock = threading.Lock()
_ingest_started = False


def _bootstrap_index_if_needed() -> None:
    """Build Chroma index in the background when the container has no vector store."""
    global _ingest_started

    if not settings.auto_ingest_on_startup:
        return

    if stats(settings).get("status") == "ok":
        return

    with _ingest_lock:
        if _ingest_started:
            return
        _ingest_started = True

    script = BACKEND_ROOT / "scripts" / "ingest_corpus.py"
    if not script.is_file():
        logger.error("Bootstrap ingest skipped: %s not found", script)
        return

    logger.info("Vector index empty — starting background corpus ingest (15 schemes + BGE embed)...")
    completed = subprocess.run(
        [sys.executable, str(script), "--force-live"],
        cwd=str(BACKEND_ROOT),
        check=False,
    )
    if completed.returncode == 0:
        logger.info("Background ingest finished: %s", stats(settings))
    else:
        logger.error("Background ingest failed (exit %s)", completed.returncode)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    thread = threading.Thread(
        target=_bootstrap_index_if_needed,
        name="bootstrap-ingest",
        daemon=True,
    )
    thread.start()
    yield


app = FastAPI(
    title="Mutual Fund FAQ Assistant",
    description="Facts-only RAG FAQ assistant for Tata Mutual Fund schemes on Groww.",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(schemes.router, prefix="/api", tags=["schemes"])
app.include_router(ingest.router, prefix="/api", tags=["ingest"])


@app.get("/")
def root() -> dict:
    index = stats()
    status = "ok" if index.get("status") == "ok" else "degraded"
    payload: dict = {
        "service": "mutual-fund-faq-assistant",
        "status": status,
        "index": index,
        "docs": "/docs",
        "health": "/api/health",
    }
    if settings.auto_ingest_on_startup and index.get("status") != "ok" and _ingest_started:
        payload["ingest"] = "running"
    return payload
