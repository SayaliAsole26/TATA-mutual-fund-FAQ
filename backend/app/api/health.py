"""GET /api/health"""

from __future__ import annotations

from fastapi import APIRouter

from app.ingestion.embed_index import stats

router = APIRouter()


@router.get("/health")
def get_health() -> dict:
    index = stats()
    status = "ok" if index.get("status") == "ok" else "degraded"
    return {"status": status, "index": index}
