"""Tests for BGE-large embedding index (Phase 1.1.3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ingestion.embed_index import (
    BGE_QUERY_INSTRUCTION,
    COLLECTION_NAME,
    embed_passages,
    embed_query,
    index_scheme,
    load_all_chunk_records,
    rebuild_index,
    reset_clients,
    search,
    stats,
)


@pytest.fixture
def sample_chunks() -> list[dict]:
    return [
        {
            "chunk_id": "scheme-a__expense_ratio__0",
            "scheme_id": "scheme-a",
            "scheme_name": "Scheme A",
            "source_url": "https://groww.in/mutual-funds/scheme-a",
            "section": "expense_ratio",
            "section_label": "Expense ratio",
            "content": "Expense ratio: 1.00%",
            "extracted_at": "2027-06-18T00:00:00+00:00",
            "chunk_index": 0,
            "chunk_source": "processed",
        },
        {
            "chunk_id": "scheme-a__min_sip__0",
            "scheme_id": "scheme-a",
            "scheme_name": "Scheme A",
            "source_url": "https://groww.in/mutual-funds/scheme-a",
            "section": "min_sip",
            "section_label": "Minimum SIP",
            "content": "Minimum SIP amount: ₹500",
            "extracted_at": "2027-06-18T00:00:00+00:00",
            "chunk_index": 0,
            "chunk_source": "processed",
        },
        {
            "chunk_id": "scheme-b__expense_ratio__0",
            "scheme_id": "scheme-b",
            "scheme_name": "Scheme B",
            "source_url": "https://groww.in/mutual-funds/scheme-b",
            "section": "expense_ratio",
            "section_label": "Expense ratio",
            "content": "Expense ratio: 0.50%",
            "extracted_at": "2027-06-18T00:00:00+00:00",
            "chunk_index": 0,
            "chunk_source": "processed",
        },
    ]


@pytest.fixture
def fake_embed_fn():
    def _embed(texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            seed = sum(ord(c) for c in text) % 997
            vectors.append([float(seed + i) / 1000.0 for i in range(8)])
        return vectors

    return _embed


@pytest.fixture
def corpus_dirs(tmp_path: Path, sample_chunks: list[dict]) -> tuple[Path, Path]:
    processed = tmp_path / "processed"
    processed.mkdir()
    index_dir = tmp_path / "index"

    for scheme_id in ("scheme-a", "scheme-b"):
        scheme_chunks = [c for c in sample_chunks if c["scheme_id"] == scheme_id]
        payload = {
            "scheme_id": scheme_id,
            "chunk_count": len(scheme_chunks),
            "generated_at": "2027-06-18T00:00:00+00:00",
            "chunks": scheme_chunks,
        }
        (processed / f"{scheme_id}_chunks.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    return processed, index_dir


class FakeSettings:
    def __init__(self, processed_dir: Path, index_dir: Path) -> None:
        self.processed_dir = processed_dir
        self.index_dir = index_dir
        self.data_dir = processed_dir.parent
        self.embedding_model_large = "test-model"
        self.embedding_model_small = "test-model-small"


@pytest.fixture(autouse=True)
def _reset_embed_clients() -> None:
    reset_clients()
    yield
    reset_clients()


def test_load_all_chunk_records(corpus_dirs: tuple[Path, Path]) -> None:
    processed, _ = corpus_dirs
    settings = FakeSettings(processed, processed.parent / "index")
    records = load_all_chunk_records(settings)  # type: ignore[arg-type]
    assert len(records) == 3


def test_rebuild_index_creates_vectors(
    corpus_dirs: tuple[Path, Path],
    fake_embed_fn,
) -> None:
    processed, index_dir = corpus_dirs
    settings = FakeSettings(processed, index_dir)

    result = rebuild_index(settings=settings, embed_fn=fake_embed_fn)  # type: ignore[arg-type]
    assert result["status"] == "ok"
    assert result["chunk_count"] == 3
    assert result["scheme_count"] == 2
    assert index_dir.is_dir()
    assert any(index_dir.iterdir())

    index_stats = stats(settings)  # type: ignore[arg-type]
    assert index_stats["status"] == "ok"
    assert index_stats["chunk_count"] == 3
    assert index_stats["collection"] == COLLECTION_NAME


def test_index_scheme_replaces_scheme_chunks(
    corpus_dirs: tuple[Path, Path],
    fake_embed_fn,
    sample_chunks: list[dict],
) -> None:
    processed, index_dir = corpus_dirs
    settings = FakeSettings(processed, index_dir)
    rebuild_index(settings=settings, embed_fn=fake_embed_fn)  # type: ignore[arg-type]

    # Update scheme-a chunks: drop min_sip
    scheme_a_chunks = [c for c in sample_chunks if c["scheme_id"] == "scheme-a"][:1]
    payload = {
        "scheme_id": "scheme-a",
        "chunk_count": 1,
        "generated_at": "2027-06-18T00:00:00+00:00",
        "chunks": scheme_a_chunks,
    }
    (processed / "scheme-a_chunks.json").write_text(json.dumps(payload), encoding="utf-8")

    index_scheme("scheme-a", settings=settings, embed_fn=fake_embed_fn)  # type: ignore[arg-type]
    index_stats = stats(settings)  # type: ignore[arg-type]
    assert index_stats["chunk_count"] == 2  # scheme-a (1) + scheme-b (1)


def test_search_filters_by_scheme(
    corpus_dirs: tuple[Path, Path],
    fake_embed_fn,
) -> None:
    processed, index_dir = corpus_dirs
    settings = FakeSettings(processed, index_dir)
    rebuild_index(settings=settings, embed_fn=fake_embed_fn)  # type: ignore[arg-type]

    hits = search(
        "expense ratio",
        scheme_id="scheme-a",
        k=3,
        settings=settings,  # type: ignore[arg-type]
        embed_fn=fake_embed_fn,
    )
    assert hits
    assert all(h["metadata"]["scheme_id"] == "scheme-a" for h in hits)


def test_embed_query_adds_instruction(fake_embed_fn) -> None:
    seen: list[str] = []

    def capture(texts: list[str]) -> list[list[float]]:
        seen.extend(texts)
        return fake_embed_fn(texts)

    embed_query("minimum SIP amount", embed_fn=capture)
    assert seen == [f"{BGE_QUERY_INSTRUCTION}minimum SIP amount"]


def test_stats_empty_index(tmp_path: Path) -> None:
    settings = FakeSettings(tmp_path / "processed", tmp_path / "index")
    (tmp_path / "processed").mkdir(parents=True)
    result = stats(settings)  # type: ignore[arg-type]
    assert result["status"] == "empty"
    assert result["chunk_count"] == 0


def test_rebuild_index_requires_chunks(tmp_path: Path) -> None:
    settings = FakeSettings(tmp_path / "processed", tmp_path / "index")
    settings.processed_dir.mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        rebuild_index(settings=settings)  # type: ignore[arg-type]
