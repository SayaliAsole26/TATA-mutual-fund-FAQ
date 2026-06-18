"""GET /api/health"""

from __future__ import annotations

from fastapi import APIRouter

from app.ingestion.embed_index import stats
from config.settings import get_settings

try:
    from app.core import bootstrap_ingest
except ImportError:  # pragma: no cover
    bootstrap_ingest = None

router = APIRouter()


def build_health_payload() -> dict:
    """Shared health payload for /api/health and /. Never exposes secrets."""
    settings = get_settings()
    index = stats(settings)
    groq_configured = bool(settings.groq_api_key.strip())

    issues: list[str] = []
    if index.get("status") != "ok":
        issues.append("index")
    if not groq_configured:
        issues.append("groq_api_key")

    payload = {
        "status": "ok" if not issues else "degraded",
        "index": index,
        "llm": {
            "provider": "groq",
            "configured": groq_configured,
            "model": settings.groq_model,
        },
        "issues": issues,
    }
    if bootstrap_ingest is not None and settings.auto_ingest_on_startup:
        ingest_state = bootstrap_ingest.snapshot()
        if ingest_state["status"] != "idle":
            payload["ingest"] = ingest_state
    return payload


@router.get("/health")
def get_health() -> dict:
    return build_health_payload()
