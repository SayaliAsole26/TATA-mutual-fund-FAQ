# Data directory layout

Use these folders to manually verify each stage of the ingestion pipeline.

| Folder | Purpose | Example files |
|--------|---------|----------------|
| **`raw/`** | Groww page snapshots (HTML, cleaned text, manifest) | `tata-elss-fund-direct-growth.html`, `.json`, `.cleaned.txt` |
| **`processed/`** | Parsed sections, structured fields, and chunks (human-readable JSON) | `tata-elss-fund-direct-growth.json`, `schemes.json` |
| **`index/`** | ChromaDB vector index (BGE-large) + readable export | `chroma.sqlite3`, `chromadb/manifest.json` |

**Raw file trio (per scheme)**

| File | Purpose |
|------|---------|
| `<scheme_id>.html` | Full HTML response from Groww |
| `<scheme_id>.cleaned.txt` | Cleaned plain text (scripts/styles removed) with source header — easy manual review |
| `<scheme_id>.json` | Fetch manifest: `source_url`, `fetched_at`, `html_file`, `cleaned_file` |

**Root files**

- `corpus_registry.json` — list of 15 schemes, URLs, and `last_ingested_at`

**Quick check**

1. After fetch: open `raw/<scheme_id>.html`, `raw/<scheme_id>.cleaned.txt`, and `raw/<scheme_id>.json`
2. After parse: open `processed/<scheme_id>.json`
3. After chunk: `cd backend && python scripts/preview_chunks.py --all`
4. After embed: `cd backend && python scripts/preview_embed.py --all`
5. Inspect embeddings: `cd backend && python scripts/export_index_manifest.py` → `data/index/chromadb/`

```bash
cd backend

# One scheme
python scripts/preview_ingest.py tata-elss-fund-direct-growth

# All 15 schemes (re-fetch live HTML + cleaned.txt + JSON)
python scripts/preview_ingest.py --all --force-live

# Regenerate cleaned.txt from existing HTML only (no network)
python scripts/backfill_cleaned.py

# List all scheme IDs
python scripts/preview_ingest.py --list

# Build BGE-large vector index from chunks
python scripts/preview_embed.py --all
python scripts/preview_embed.py --stats
python scripts/preview_embed.py --query "expense ratio" --scheme tata-elss-fund-direct-growth
```
