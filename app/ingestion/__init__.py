"""Ingestion pipeline: fetch and parse Groww scheme pages."""

from app.ingestion.chunker import (
    Chunk,
    build_embed_text,
    chunk_all_schemes,
    chunk_and_save_scheme,
    chunk_scheme,
    load_scheme_chunks,
    save_all_scheme_chunks,
    save_scheme_chunks,
)
from app.ingestion.embed_index import (
    embed_passages,
    embed_query,
    export_index_manifest,
    index_scheme,
    rebuild_index,
    search,
    stats,
)
from app.ingestion.fetcher import FetchedContent, fetch_live, fetch_scheme, load_snapshot, save_snapshot
from app.ingestion.parser import ParsedSchemeDocument, parse_scheme_content
from app.ingestion.processed_store import (
    load_processed_document,
    save_processed_document,
    update_schemes_metadata,
)

__all__ = [
    "Chunk",
    "FetchedContent",
    "ParsedSchemeDocument",
    "build_embed_text",
    "chunk_all_schemes",
    "chunk_and_save_scheme",
    "chunk_scheme",
    "embed_passages",
    "embed_query",
    "export_index_manifest",
    "fetch_live",
    "fetch_scheme",
    "index_scheme",
    "load_processed_document",
    "load_scheme_chunks",
    "load_snapshot",
    "parse_scheme_content",
    "rebuild_index",
    "save_all_scheme_chunks",
    "save_processed_document",
    "save_scheme_chunks",
    "save_snapshot",
    "search",
    "stats",
    "update_schemes_metadata",
]