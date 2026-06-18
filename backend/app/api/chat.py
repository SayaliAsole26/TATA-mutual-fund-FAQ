"""POST /api/chat"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.schemas import ChatRequest
from app.core.orchestrator import handle_chat

router = APIRouter()


@router.post("/chat")
def post_chat(body: ChatRequest) -> dict:
    return handle_chat(body.message)
