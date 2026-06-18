"""Hybrid 3-tier retrieval for FAQ chunks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.intent import (
    detect_intent_section,
    is_nav_query,
    is_structured_section,
    sections_for_broad_search,
)
from app.ingestion.chunker import SECTION_LABELS
from app.ingestion.embed_index import embed_query, get_collection, stats
from app.core.corpus_registry import SchemeEntry, get_scheme_by_id
from config.settings import Settings, get_settings

RetrievalSource = Literal["structured", "vector_section", "vector_broad", "none"]


@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    section: str
    scheme_id: str
    scheme_name: str
    source_url: str
    extracted_at: str
    chunk_source: str = "processed"
    section_label: str = ""
    distance: float | None = None

    def __post_init__(self) -> None:
        if not self.section_label:
            self.section_label = SECTION_LABELS.get(self.section, self.section)


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk] = field(default_factory=list)
    source: RetrievalSource = "none"
    scheme_id: str | None = None
    scheme_name: str | None = None
    intent_section: str | None = None
    weak_match: bool = False


def _load_scheme_metadata(scheme_id: str, settings: Settings) -> dict[str, Any] | None:
    path = settings.schemes_metadata_path
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("schemes", {}).get(scheme_id)


def _structured_chunk(
    scheme: SchemeEntry,
    section: str,
    value: str,
    metadata: dict[str, Any],
) -> RetrievedChunk:
    label = SECTION_LABELS.get(section, section)
    return RetrievedChunk(
        chunk_id=f"{scheme.scheme_id}__{section}__structured",
        content=f"{label}: {value}",
        section=section,
        scheme_id=scheme.scheme_id,
        scheme_name=scheme.scheme_name,
        source_url=scheme.source_url,
        extracted_at=str(metadata.get("last_ingested_at", "")),
        chunk_source="structured",
        section_label=label,
        distance=0.0,
    )


def _try_structured(
    scheme: SchemeEntry,
    section: str,
    settings: Settings,
) -> RetrievedChunk | None:
    metadata = _load_scheme_metadata(scheme.scheme_id, settings)
    if not metadata:
        return None
    value = metadata.get(section)
    if not value or not str(value).strip():
        return None
    return _structured_chunk(scheme, section, str(value), metadata)


def _vector_search(
    query: str,
    *,
    scheme_id: str,
    section: str | None = None,
    k: int,
    settings: Settings,
) -> list[RetrievedChunk]:
    collection = get_collection(settings)
    if collection.count() == 0:
        return []

    where: dict[str, Any] = {"scheme_id": scheme_id}
    if section:
        where = {"$and": [{"scheme_id": scheme_id}, {"section": section}]}

    query_vector = embed_query(query, settings=settings)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(k, collection.count()),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits: list[RetrievedChunk] = []
    ids = (results.get("ids") or [[]])[0]
    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        meta = metadata or {}
        hits.append(
            RetrievedChunk(
                chunk_id=str(chunk_id),
                content=str(document),
                section=str(meta.get("section", "")),
                scheme_id=str(meta.get("scheme_id", scheme_id)),
                scheme_name=str(meta.get("scheme_name", "")),
                source_url=str(meta.get("source_url", "")),
                extracted_at=str(meta.get("extracted_at", "")),
                chunk_source=str(meta.get("chunk_source", "processed")),
                section_label=str(meta.get("section_label", "")),
                distance=float(distance) if distance is not None else None,
            )
        )
    return hits


def _dedupe_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    by_section: dict[str, RetrievedChunk] = {}
    for chunk in chunks:
        existing = by_section.get(chunk.section)
        if existing is None:
            by_section[chunk.section] = chunk
            continue
        if existing.chunk_source != "processed" and chunk.chunk_source == "processed":
            by_section[chunk.section] = chunk
            continue
        if chunk.distance is not None and (
            existing.distance is None or chunk.distance < existing.distance
        ):
            by_section[chunk.section] = chunk
    return list(by_section.values())


def _filter_nav(chunks: list[RetrievedChunk], message: str) -> list[RetrievedChunk]:
    if is_nav_query(message):
        return chunks
    return [c for c in chunks if c.section != "nav"]


def retrieve(
    query: str,
    scheme: SchemeEntry,
    *,
    intent_section: str | None = None,
    settings: Settings | None = None,
) -> RetrievalResult:
    """
    Three-tier retrieval for a resolved scheme.

    Tier 1: structured metadata in schemes.json
    Tier 2: vector search with scheme_id + section
    Tier 3: vector search with scheme_id only
    """
    settings = settings or get_settings()
    section = intent_section or detect_intent_section(query)

    if section == "nav" and not is_nav_query(query):
        section = None

    result = RetrievalResult(
        scheme_id=scheme.scheme_id,
        scheme_name=scheme.scheme_name,
        intent_section=section,
    )

    index_status = stats(settings)
    if index_status.get("status") != "ok" and not settings.schemes_metadata_path.is_file():
        return result

    # Tier 1 — structured short-circuit
    if section and is_structured_section(section):
        structured = _try_structured(scheme, section, settings)
        if structured:
            result.chunks = [structured]
            result.source = "structured"
            return result

    chunks: list[RetrievedChunk] = []

    # Tier 2 — section-filtered vector
    if section:
        chunks = _vector_search(query, scheme_id=scheme.scheme_id, section=section, k=2, settings=settings)

    # Tier 3 — broad vector
    if not chunks:
        k = sections_for_broad_search(section)
        chunks = _vector_search(query, scheme_id=scheme.scheme_id, section=None, k=k, settings=settings)
        result.source = "vector_broad"
    else:
        result.source = "vector_section"

    chunks = _filter_nav(chunks, query)
    chunks = _dedupe_chunks(chunks)

    if chunks:
        best = min(c.distance for c in chunks if c.distance is not None)
        if best > settings.retrieval_max_distance:
            result.weak_match = True
            # Retry structured for detected section if vector match is weak
            if section and is_structured_section(section):
                structured = _try_structured(scheme, section, settings)
                if structured:
                    result.chunks = [structured]
                    result.source = "structured"
                    result.weak_match = False
                    return result
    else:
        result.weak_match = True

    result.chunks = chunks
    return result


def get_scheme_entry(scheme_id: str) -> SchemeEntry | None:
    return get_scheme_by_id(scheme_id)
