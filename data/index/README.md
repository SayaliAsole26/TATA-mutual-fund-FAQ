# ChromaDB vector index (`data/index/`)

BGE-large embeddings for all FAQ chunks are stored here by `embed_index.py`.

## On-disk layout (Chroma persistent client)

| Path | Purpose |
|------|---------|
| `chroma.sqlite3` | Chroma metadata DB (collection, chunk IDs, document text, metadata) |
| `<uuid>/data_level0.bin` | HNSW vector index (1024-d floats from `BAAI/bge-large-en-v1.5`) |
| `<uuid>/header.bin`, `length.bin`, `link_lists.bin` | HNSW index internals |
| `chromadb/` | **Human-readable export** (generated; safe to open in IDE) |

Collection name: **`tata_mf_faq_chunks`** (cosine similarity).

## Human-readable export (`chromadb/`)

Binary embeddings are hard to inspect directly. Export a JSON manifest:

```bash
python scripts/export_index_manifest.py
```

This writes:

| File | Contents |
|------|----------|
| `chromadb/manifest.json` | All 181 chunks: metadata, `content`, `embedding_dim`, `embedding_preview` |
| `chromadb/by_scheme/<scheme_id>.json` | Chunks grouped per scheme |

Use `--full-vectors` only if you need all 1024 dimensions in JSON (large file).

## Verify index

```bash
python scripts/preview_embed.py --stats
python scripts/preview_embed.py --query "expense ratio" --scheme tata-elss-fund-direct-growth
python -c "from app.ingestion.embed_index import stats; import json; print(json.dumps(stats(), indent=2))"
```

## Rebuild index

```bash
python scripts/preview_embed.py --all
python scripts/export_index_manifest.py
```

Full pipeline (fetch → parse → chunk → embed):

```bash
python scripts/ingest_corpus.py
```
