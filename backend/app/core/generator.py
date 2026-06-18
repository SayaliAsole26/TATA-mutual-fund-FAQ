"""Groq LLM generation for factual answers."""

from __future__ import annotations

import logging

from groq import Groq

from app.core.prompts import STRICT_SYSTEM_PROMPT, SYSTEM_PROMPT, build_user_prompt
from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def generate_answer(
    *,
    user_message: str,
    scheme_name: str,
    scheme_id: str,
    assembled_chunk_context: str,
    settings: Settings | None = None,
    strict: bool = False,
) -> str:
    """Call Groq chat completion with the constrained system prompt."""
    settings = settings or get_settings()
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    client = Groq(api_key=settings.groq_api_key)
    user_prompt = build_user_prompt(
        user_message=user_message,
        scheme_name=scheme_name,
        scheme_id=scheme_id,
        assembled_chunk_context=assembled_chunk_context,
    )

    system_prompt = STRICT_SYSTEM_PROMPT if strict else SYSTEM_PROMPT

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=settings.groq_temperature,
        max_tokens=512,
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Groq returned empty completion")
    return content.strip()
