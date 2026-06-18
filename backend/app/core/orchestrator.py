"""End-to-end query pipeline: detect → retrieve → generate → format."""

from __future__ import annotations

import logging
from typing import Any

from app.core.context import assemble_context
from app.core.formatter import build_formatted_answer, format_from_structured, normalize_llm_output
from app.core.generator import generate_answer
from app.core.guardrails import classify_input, repair_output, validate_output
from app.core.intent import detect_intent_section
from app.core.retriever import retrieve
from app.core.scheme_aliases import resolve_scheme, scheme_needs_clarification
from app.core.corpus_registry import SchemeEntry, load_corpus_registry
from app.core.templates import refusal_response
from app.ingestion.embed_index import stats
from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

FALLBACK_TEMPLATE = (
    "I can only share verified facts from official scheme sources. "
    "I could not find a confident match for your question in the ingested corpus. "
    "Please see the scheme page for details."
)


def _clarification_response() -> dict[str, Any]:
    schemes = load_corpus_registry()
    examples = ", ".join(s.scheme_name for s in schemes[:4])
    return {
        "type": "clarification",
        "message": (
            "Which Tata Mutual Fund scheme do you mean? "
            f"For example: {examples}, …"
        ),
        "schemes": [s.scheme_id for s in schemes],
    }


def _fallback_answer(scheme_name: str, source_url: str, extracted_at: str) -> str:
    return build_formatted_answer(FALLBACK_TEMPLATE, source_url, extracted_at)


def _refusal_from_guardrail(message: str, reason: str) -> dict[str, Any]:
    scheme = resolve_scheme(message)
    return refusal_response(
        reason,
        scheme_name=scheme.scheme_name if scheme else "",
        scheme_url=scheme.source_url if scheme else "",
    )


def _finalize_factual_answer(
    answer: str,
    *,
    scheme: SchemeEntry,
    primary_url: str,
    primary_date: str,
    normalized: str,
    context: str,
    settings: Settings,
) -> str:
    """Validate output; regenerate once if needed; then repair or fallback."""
    validation = validate_output(answer)
    if validation.valid:
        return answer

    if settings.groq_api_key:
        try:
            raw = generate_answer(
                user_message=normalized,
                scheme_name=scheme.scheme_name,
                scheme_id=scheme.scheme_id,
                assembled_chunk_context=context,
                settings=settings,
                strict=True,
            )
            retried = normalize_llm_output(raw, primary_url, primary_date)
            if validate_output(retried).valid:
                return retried
            answer = retried
        except Exception as exc:
            logger.warning("Strict regeneration failed: %s", exc)

    repaired = repair_output(answer, fallback_url=primary_url, fallback_date=primary_date)
    if validate_output(repaired).valid:
        return repaired

    return _fallback_answer(scheme.scheme_name, primary_url, primary_date)


def handle_chat(message: str, *, settings: Settings | None = None) -> dict[str, Any]:
    """Process a user chat message and return API JSON."""
    settings = settings or get_settings()
    normalized = " ".join(message.split())
    if not normalized:
        return {
            "type": "error",
            "message": "Please enter a question about one of the 15 Tata Mutual Fund schemes.",
        }

    index_status = stats(settings)
    if index_status.get("status") not in {"ok", "empty"}:
        logger.warning("Index status: %s", index_status)

    if index_status.get("status") == "empty":
        return {
            "type": "error",
            "message": "Corpus not indexed yet. Please try again after ingestion completes.",
        }

    guard = classify_input(normalized)
    if guard.blocked and guard.reason:
        if guard.reason == "pii":
            logger.info("Chat input refused: reason=pii")
        else:
            logger.info("Chat input refused: reason=%s", guard.reason)
        return _refusal_from_guardrail(normalized, guard.reason)

    scheme = resolve_scheme(normalized)
    if scheme_needs_clarification(normalized, scheme):
        return _clarification_response()

    if scheme is None:
        return _clarification_response()

    intent_section = detect_intent_section(normalized)
    retrieval = retrieve(normalized, scheme, intent_section=intent_section, settings=settings)

    if not retrieval.chunks or retrieval.weak_match:
        return {
            "type": "answer",
            "answer": _fallback_answer(
                scheme.scheme_name,
                scheme.source_url,
                scheme.last_ingested_at or "",
            ),
            "scheme_id": scheme.scheme_id,
            "scheme_name": scheme.scheme_name,
            "source_url": scheme.source_url,
            "last_updated": scheme.last_ingested_at,
            "sections_used": [],
            "retrieval_source": retrieval.source,
        }

    primary = retrieval.chunks[0]
    sections_used = sorted({c.section for c in retrieval.chunks})

    if retrieval.source == "structured":
        answer = format_from_structured(primary, normalized)
        answer = _finalize_factual_answer(
            answer,
            scheme=scheme,
            primary_url=primary.source_url,
            primary_date=primary.extracted_at,
            normalized=normalized,
            context=assemble_context(retrieval),
            settings=settings,
        )
    else:
        context = assemble_context(retrieval)
        try:
            raw = generate_answer(
                user_message=normalized,
                scheme_name=scheme.scheme_name,
                scheme_id=scheme.scheme_id,
                assembled_chunk_context=context,
                settings=settings,
            )
            answer = normalize_llm_output(raw, primary.source_url, primary.extracted_at)
            answer = _finalize_factual_answer(
                answer,
                scheme=scheme,
                primary_url=primary.source_url,
                primary_date=primary.extracted_at,
                normalized=normalized,
                context=context,
                settings=settings,
            )
        except Exception as exc:
            logger.exception("Groq generation failed: %s", exc)
            answer = format_from_structured(primary, normalized)

    return {
        "type": "answer",
        "answer": answer,
        "scheme_id": scheme.scheme_id,
        "scheme_name": scheme.scheme_name,
        "source_url": primary.source_url,
        "last_updated": primary.extracted_at or scheme.last_ingested_at,
        "sections_used": sections_used,
        "retrieval_source": retrieval.source,
    }
