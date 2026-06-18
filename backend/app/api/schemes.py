"""GET /api/schemes"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.corpus_registry import load_corpus_registry

router = APIRouter()


@router.get("/schemes")
def get_schemes() -> dict:
    schemes = load_corpus_registry()
    return {
        "amc": "Tata Mutual Fund",
        "schemes": [
            {
                "scheme_id": s.scheme_id,
                "scheme_name": s.scheme_name,
                "source_url": s.source_url,
                "category": s.category,
            }
            for s in schemes
        ],
    }
