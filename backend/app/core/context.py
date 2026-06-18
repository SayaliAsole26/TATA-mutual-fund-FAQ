"""Assemble retrieved chunks into LLM context."""

from __future__ import annotations

from app.core.retriever import RetrievedChunk, RetrievalResult

MAX_CONTEXT_CHARS = 6000  # ~1500 tokens


def format_chunk_line(chunk: RetrievedChunk) -> str:
    return (
        f"[{chunk.section}] {chunk.content} "
        f"(source: {chunk.source_url}, updated: {chunk.extracted_at})"
    )


def assemble_context(result: RetrievalResult) -> str:
    """Build RETRIEVED CONTEXT block for the user prompt."""
    lines = [format_chunk_line(chunk) for chunk in result.chunks]
    text = "\n".join(lines)
    if len(text) <= MAX_CONTEXT_CHARS:
        return text
    return text[:MAX_CONTEXT_CHARS].rsplit("\n", 1)[0]
