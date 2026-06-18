"""FastAPI application entrypoint (Phase 2c)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, health, ingest, schemes
from config.settings import get_settings

settings = get_settings()

app = FastAPI(
    title="Mutual Fund FAQ Assistant",
    description="Facts-only RAG FAQ assistant for Tata Mutual Fund schemes on Groww.",
    version="0.3.0",
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
    return {"service": "mutual-fund-faq-assistant", "docs": "/docs"}
