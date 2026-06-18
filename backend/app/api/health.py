"""GET /api/health"""

from __future__ import annotations

from fastapi import APIRouter

from app.ingestion.embed_index import stats
from config.settings import get_settings

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

    return {
        "status": "ok" if not issues else "degraded",
        "index": index,
        "llm": {
            "provider": "groq",
            "configured": groq_configured,
            "model": settings.groq_model,
        },
        "issues": issues,
    }


@router.get("/health")
def get_health() -> dict:
    return build_health_payload()
