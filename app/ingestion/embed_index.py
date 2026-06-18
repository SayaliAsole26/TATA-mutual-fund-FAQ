"""
Batch-embed FAQ chunks with BGE-large and persist to a local Chroma index.

Phase 1.1.3 — corpus indexing at data/index/ (no embedding API cost).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import chromadb
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer

from app.ingestion.chunker import build_embed_text, load_scheme_chunks
from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "tata_mf_faq_chunks"
BGE_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
DEFAULT_BATCH_SIZE = 16

CHUNK_METADATA_KEYS = (
    "chunk_id",
    "scheme_id",
    "scheme_name",
    "source_url",
    "section",
    "section_label",
    "extracted_at",
    "chunk_index",
    "chunk_source",
    "embedding_model",
)

_chroma_client: chromadb.ClientAPI | None = None
_chroma_client_path: Path | None = None

EmbedFn = Callable[[list[str]], list[list[float]]]


@lru_cache(maxsize=2)
def _load_sentence_transformer(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def reset_clients() -> None:
    """Clear cached Chroma client and embedding model (use after index swap)."""
    global _chroma_client, _chroma_client_path
    _chroma_client = None
    _chroma_client_path = None
    _load_sentence_transformer.cache_clear()


def get_chroma_client(
    settings: Settings | None = None,
    *,
    path: Path | None = None,
) -> chromadb.ClientAPI:
    """Return a persistent Chroma client for the live or staging index path."""
    global _chroma_client, _chroma_client_path

    settings = settings or get_settings()
    target = path or settings.index_dir
    target.mkdir(parents=True, exist_ok=True)

    if _chroma_client is not None and _chroma_client_path == target.resolve():
        return _chroma_client

    _chroma_client = chromadb.PersistentClient(path=str(target))
    _chroma_client_path = target.resolve()
    return _chroma_client


def get_collection(
    settings: Settings | None = None,
    *,
    path: Path | None = None,
    create: bool = True,
) -> Collection:
    """Open (or create) the FAQ chunk collection."""
    client = get_chroma_client(settings, path=path)
    if create:
        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return client.get_collection(name=COLLECTION_NAME)


def embed_passages(
    texts: list[str],
    *,
    settings: Settings | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    embed_fn: EmbedFn | None = None,
) -> list[list[float]]:
    """Embed passage texts with BGE-large (normalized vectors)."""
    if not texts:
        return []

    if embed_fn is not None:
        return embed_fn(texts)

    settings = settings or get_settings()
    model = _load_sentence_transformer(settings.embedding_model_large)
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 32,
    )
    return vectors.tolist()


def embed_query(
    query: str,
    *,
    settings: Settings | None = None,
    embed_fn: EmbedFn | None = None,
) -> list[float]:
    """Embed a user query with the BGE retrieval instruction prefix."""
    prefixed = f"{BGE_QUERY_INSTRUCTION}{query}"
    return embed_passages([prefixed], settings=settings, embed_fn=embed_fn)[0]


def load_all_chunk_records(settings: Settings | None = None) -> list[dict[str, Any]]:
    """Load all chunk dicts from data/processed/*_chunks.json files."""
    settings = settings or get_settings()
    records: list[dict[str, Any]] = []
    for path in sorted(settings.processed_dir.glob("*_chunks.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        records.extend(payload.get("chunks") or [])
    return records


def _chunk_metadata(
    chunk: dict[str, Any],
    *,
    embedding_model: str,
) -> dict[str, str | int]:
    """Chroma-compatible metadata for one chunk."""
    meta: dict[str, str | int] = {
        "chunk_id": str(chunk["chunk_id"]),
        "scheme_id": str(chunk["scheme_id"]),
        "scheme_name": str(chunk["scheme_name"]),
        "source_url": str(chunk["source_url"]),
        "section": str(chunk["section"]),
        "section_label": str(chunk.get("section_label") or chunk["section"]),
        "extracted_at": str(chunk["extracted_at"]),
        "chunk_index": int(chunk.get("chunk_index", 0)),
        "chunk_source": str(chunk.get("chunk_source", "processed")),
        "embedding_model": embedding_model,
    }
    return meta


def _upsert_chunks(
    collection: Collection,
    chunks: list[dict[str, Any]],
    *,
    settings: Settings | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    embed_fn: EmbedFn | None = None,
) -> int:
    """Embed and upsert a batch of chunk dicts; returns count upserted."""
    if not chunks:
        return 0

    settings = settings or get_settings()
    model_name = settings.embedding_model_large

    ids = [str(c["chunk_id"]) for c in chunks]
    documents = [str(c["content"]) for c in chunks]
    metadatas = [_chunk_metadata(c, embedding_model=model_name) for c in chunks]
    embed_texts = [build_embed_text(c) for c in chunks]

    all_embeddings: list[list[float]] = []
    for start in range(0, len(embed_texts), batch_size):
        batch = embed_texts[start : start + batch_size]
        all_embeddings.extend(
            embed_passages(batch, settings=settings, batch_size=batch_size, embed_fn=embed_fn)
        )

    collection.upsert(
        ids=ids,
        embeddings=all_embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    return len(chunks)


def index_scheme(
    scheme_id: str,
    *,
    settings: Settings | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    embed_fn: EmbedFn | None = None,
) -> dict[str, Any]:
    """
    Replace all indexed chunks for one scheme.

    Deletes existing vectors for ``scheme_id``, then upserts from
    ``data/processed/<scheme_id>_chunks.json``.
    """
    settings = settings or get_settings()
    chunks = load_scheme_chunks(scheme_id, settings=settings)
    if not chunks:
        raise FileNotFoundError(
            f"No chunks found for {scheme_id!r}. Run preview_chunks.py or chunker first."
        )

    collection = get_collection(settings)
    collection.delete(where={"scheme_id": scheme_id})
    count = _upsert_chunks(
        collection,
        chunks,
        settings=settings,
        batch_size=batch_size,
        embed_fn=embed_fn,
    )
    return {
        "scheme_id": scheme_id,
        "chunk_count": count,
        "embedding_model": settings.embedding_model_large,
        "index_dir": str(settings.index_dir),
    }


def rebuild_index(
    *,
    settings: Settings | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    embed_fn: EmbedFn | None = None,
) -> dict[str, Any]:
    """
    Rebuild the full vector index from all ``*_chunks.json`` files.

    Clears the live Chroma collection, then batch-embeds and upserts all chunks.
    Suitable for this small corpus (~180 chunks); avoids Windows file-lock issues
    with directory swapping while Chroma holds SQLite handles.
    """
    settings = settings or get_settings()
    chunks = load_all_chunk_records(settings)
    if not chunks:
        raise FileNotFoundError(
            "No chunk files found under data/processed/. Run preview_chunks.py --all first."
        )

    collection = get_collection(settings)
    if collection.count() > 0:
        existing = collection.get(include=[])
        ids = existing.get("ids") or []
        for start in range(0, len(ids), 500):
            collection.delete(ids=ids[start : start + 500])

    count = _upsert_chunks(
        collection,
        chunks,
        settings=settings,
        batch_size=batch_size,
        embed_fn=embed_fn,
    )

    scheme_ids = sorted({str(c["scheme_id"]) for c in chunks})
    return {
        "status": "ok",
        "chunk_count": count,
        "scheme_count": len(scheme_ids),
        "scheme_ids": scheme_ids,
        "embedding_model": settings.embedding_model_large,
        "index_dir": str(settings.index_dir),
        "rebuilt_at": datetime.now(timezone.utc).isoformat(),
    }


def stats(settings: Settings | None = None) -> dict[str, Any]:
    """Return vector index statistics for verification and monitoring."""
    settings = settings or get_settings()
    if not settings.index_dir.is_dir() or not any(settings.index_dir.iterdir()):
        return {
            "status": "empty",
            "chunk_count": 0,
            "scheme_count": 0,
            "embedding_model": settings.embedding_model_large,
            "index_dir": str(settings.index_dir),
        }

    try:
        collection = get_collection(settings)
    except Exception as exc:
        logger.warning("Could not open collection: %s", exc)
        return {
            "status": "missing_collection",
            "chunk_count": 0,
            "scheme_count": 0,
            "embedding_model": settings.embedding_model_large,
            "index_dir": str(settings.index_dir),
        }

    total = collection.count()
    if total == 0:
        return {
            "status": "empty",
            "chunk_count": 0,
            "scheme_count": 0,
            "embedding_model": settings.embedding_model_large,
            "index_dir": str(settings.index_dir),
            "collection": COLLECTION_NAME,
        }

    sample = collection.get(limit=total, include=["metadatas"])
    scheme_ids = sorted(
        {str(m["scheme_id"]) for m in (sample.get("metadatas") or []) if m.get("scheme_id")}
    )
    return {
        "status": "ok",
        "chunk_count": total,
        "scheme_count": len(scheme_ids),
        "scheme_ids": scheme_ids,
        "embedding_model": settings.embedding_model_large,
        "index_dir": str(settings.index_dir),
        "collection": COLLECTION_NAME,
    }


def search(
    query: str,
    *,
    scheme_id: str | None = None,
    k: int = 5,
    settings: Settings | None = None,
    embed_fn: EmbedFn | None = None,
) -> list[dict[str, Any]]:
    """Similarity search for verification and Phase 2 retriever prototyping."""
    settings = settings or get_settings()
    collection = get_collection(settings)
    if collection.count() == 0:
        return []

    query_vector = embed_query(query, settings=settings, embed_fn=embed_fn)
    where = {"scheme_id": scheme_id} if scheme_id else None

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(k, collection.count()),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits: list[dict[str, Any]] = []
    ids = (results.get("ids") or [[]])[0]
    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        hits.append(
            {
                "chunk_id": chunk_id,
                "content": document,
                "metadata": metadata,
                "distance": distance,
            }
        )
    return hits


def export_index_manifest(
    *,
    settings: Settings | None = None,
    output_dir: Path | None = None,
    preview_dims: int = 8,
    include_full_vectors: bool = False,
) -> Path:
    """
    Export a human-readable view of the Chroma index to ``data/index/chromadb/``.

    Binary vectors remain in ``chroma.sqlite3``; this writes JSON you can open in the
    IDE: a corpus ``manifest.json`` plus per-scheme files under ``by_scheme/``.
    """
    settings = settings or get_settings()
    out_dir = output_dir or (settings.index_dir / "chromadb")
    out_dir.mkdir(parents=True, exist_ok=True)
    by_scheme_dir = out_dir / "by_scheme"
    by_scheme_dir.mkdir(parents=True, exist_ok=True)

    collection = get_collection(settings)
    total = collection.count()
    if total == 0:
        raise RuntimeError("Vector index is empty. Run preview_embed.py --all first.")

    payload = collection.get(
        limit=total,
        include=["embeddings", "documents", "metadatas"],
    )

    ids = payload.get("ids") or []
    embeddings = payload.get("embeddings")
    documents = payload.get("documents")
    metadatas = payload.get("metadatas")
    if embeddings is None:
        embeddings = []
    if documents is None:
        documents = []
    if metadatas is None:
        metadatas = []

    records: list[dict[str, Any]] = []
    by_scheme: dict[str, list[dict[str, Any]]] = {}

    for chunk_id, embedding, document, metadata in zip(ids, embeddings, documents, metadatas):
        if embedding is None:
            continue
        record: dict[str, Any] = {
            "chunk_id": chunk_id,
            "content": document,
            "embedding_dim": len(embedding),
            "embedding_preview": [round(float(v), 6) for v in embedding[:preview_dims]],
            **(metadata or {}),
        }
        if include_full_vectors:
            record["embedding"] = [round(float(v), 6) for v in embedding]
        records.append(record)
        scheme_id = str((metadata or {}).get("scheme_id", "unknown"))
        by_scheme.setdefault(scheme_id, []).append(record)

    index_stats = stats(settings)
    manifest = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "vector_store": "chromadb",
        "collection": COLLECTION_NAME,
        "index_dir": str(settings.index_dir),
        "chroma_files": {
            "sqlite": "chroma.sqlite3",
            "hnsw_segment": "UUID subfolder with data_level0.bin (1024-d BGE-large vectors)",
        },
        "chunk_count": len(records),
        "scheme_count": len(by_scheme),
        "embedding_model": index_stats.get("embedding_model"),
        "note": (
            "embedding_preview shows the first "
            f"{preview_dims} of {records[0]['embedding_dim'] if records else 1024} "
            "dimensions. Full vectors live in chroma.sqlite3."
        ),
        "chunks": records,
    }

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    for scheme_id, scheme_chunks in sorted(by_scheme.items()):
        scheme_path = by_scheme_dir / f"{scheme_id}.json"
        scheme_path.write_text(
            json.dumps(
                {
                    "scheme_id": scheme_id,
                    "chunk_count": len(scheme_chunks),
                    "chunks": scheme_chunks,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    logger.info("Exported %d chunks to %s", len(records), out_dir)
    return manifest_path
