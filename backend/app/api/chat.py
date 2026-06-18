"""POST /api/chat"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from app.api.schemas import ChatRequest
from app.core.intent import detect_intent_section
from app.core.orchestrator import handle_chat
from app.core.scheme_aliases import resolve_scheme

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat")
def post_chat(body: ChatRequest, request: Request) -> dict:
    message = body.message.strip()
    scheme = resolve_scheme(message) if message else None
    intent = detect_intent_section(message) if message else None
    logger.info(
        "chat request intent=%s scheme_id=%s ip=%s",
        intent or "none",
        scheme.scheme_id if scheme else "none",
        request.client.host if request.client else "unknown",
    )
    return handle_chat(body.message)
