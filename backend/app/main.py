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
from app.api.health import build_health_payload
from app.core import bootstrap_ingest
from app.ingestion.embed_index import stats
from app.middleware.rate_limit import ChatRateLimitMiddleware
from config.settings import BACKEND_ROOT, get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

if not settings.groq_api_key.strip():
    logger.warning(
        "GROQ_API_KEY is not set — set it in Railway variables for LLM-generated answers"
    )

_ingest_lock = threading.Lock()


def _run_logged_ingest(args: list[str]) -> tuple[int, str]:
    """Run ingest script and stream stdout/stderr into container logs."""
    script = BACKEND_ROOT / "scripts" / "ingest_corpus.py"
    process = subprocess.Popen(
        [sys.executable, str(script), *args],
        cwd=str(BACKEND_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    tail: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        line = line.rstrip()
        if line:
            logger.info("[ingest] %s", line)
            tail.append(line)
            if len(tail) > 40:
                tail.pop(0)
    return process.wait(), "\n".join(tail)


def _bootstrap_index_if_needed() -> None:
    """Build Chroma index in the background when the container has no vector store."""
    if not settings.auto_ingest_on_startup:
        return

    if stats(settings).get("status") == "ok":
        return

    chunk_files = list(settings.processed_dir.glob("*_chunks.json"))
    if chunk_files:
        mode = "embed_only"
        ingest_args = ["--embed-only"]
    else:
        mode = "force_live"
        ingest_args = ["--force-live"]

    with _ingest_lock:
        if not bootstrap_ingest.mark_running(mode):
            return

    logger.info(
        "Vector index empty — starting background ingest (%s, %d chunk file(s))...",
        mode,
        len(chunk_files),
    )
    exit_code, log_tail = _run_logged_ingest(ingest_args)
    from app.ingestion.embed_index import reset_clients

    reset_clients()
    bootstrap_ingest.mark_finished(exit_code, stderr_tail=log_tail)
    if exit_code == 0:
        logger.info("Background ingest finished: %s", stats(settings))
    else:
        logger.error("Background ingest failed (exit %s)", exit_code)


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

app.add_middleware(ChatRateLimitMiddleware)
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
    payload = build_health_payload()
    payload.update(
        {
            "service": "mutual-fund-faq-assistant",
            "docs": "/docs",
            "health": "/api/health",
        }
    )
    ingest_state = bootstrap_ingest.snapshot()
    if (
        settings.auto_ingest_on_startup
        and ingest_state["status"] in ("running", "succeeded", "failed")
        and payload["index"].get("status") != "ok"
    ):
        payload["ingest"] = ingest_state
    return payload
