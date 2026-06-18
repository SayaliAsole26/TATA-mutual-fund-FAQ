# Backend — Mutual Fund FAQ Assistant

Python / FastAPI RAG backend for the Tata Mutual Fund facts-only FAQ assistant (15 Groww scheme pages).

## Setup (Phase 2)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
cp .env.example .env            # add GROQ_API_KEY
```

**Prerequisites**

1. **Indexed corpus** — shared `data/` folder at repo root. Run ingestion once if `data/index/` is empty:
   ```bash
   cd backend
   python scripts/ingest_corpus.py
   ```
2. **Groq API key** — set `GROQ_API_KEY` in `backend/.env` (or repo-root `.env`) for vector-backed answers.

## Run API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

- Interactive docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

## Environment

| Variable | Example | Purpose |
|----------|---------|---------|
| `GROQ_API_KEY` | `gsk_…` | Groq LLM generation |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Chat model |
| `GROQ_TEMPERATURE` | `0.1` | Low temperature for factual answers |
| `EMBEDDING_MODEL_LARGE` | `BAAI/bge-large-en-v1.5` | Index + query embeddings (1024-d) |
| `RETRIEVAL_MAX_DISTANCE` | `0.55` | Weak-match threshold (cosine distance) |
| `CORS_ORIGINS` | `http://localhost:5173` | Stitch / Vite frontend dev origin |
| `TIMEZONE` | `Asia/Kolkata` | Daily ingest scheduler (10:00 IST) |

See `backend/.env.example` for the full list.

## API endpoints

| Method | Path | Handler |
|--------|------|---------|
| `POST` | `/api/chat` | `app/api/chat.py` → `orchestrator.handle_chat()` |
| `GET` | `/api/health` | `app/api/health.py` — index stats |
| `GET` | `/api/schemes` | `app/api/schemes.py` — 15 Tata schemes |
| `POST` | `/api/ingest` | `app/api/ingest.py` — admin re-index (`X-Admin-Key`) |
| `GET` | `/` | Service info + link to `/docs` |

Phase 3 guardrails return `type: refusal` with `reason` (`advisory`, `comparative`, `pii`, `performance`, `out_of_corpus`).

### `POST /api/chat` example

```bash
curl -X POST http://localhost:8000/api/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"What is the minimum SIP for Tata ELSS?\"}"
```

Response types: `answer` | `clarification` | `refusal` | `error`

## Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI entrypoint (CORS, routers)
│   ├── api/                    # Thin HTTP layer
│   ├── core/                   # RAG pipeline (retriever, orchestrator, …)
│   └── ingestion/              # Corpus fetch, parse, chunk, embed
├── config/
│   └── settings.py
├── scripts/                    # ingest_corpus.py, preview_*, export_*
├── scheduler/                  # daily_ingest_job.py (10:00 IST)
├── tests/
└── requirements.txt
```

Shared corpus data: `../data/` (repo root).

## Tests & ingestion

```bash
cd backend
python scripts/ingest_corpus.py
python scripts/export_index_manifest.py
```

### Scheduled ingest (GitHub Actions)

Daily at **10:00 IST** via [`.github/workflows/daily-ingest.yml`](../.github/workflows/daily-ingest.yml):

| Trigger | How |
|---------|-----|
| Automatic | `cron: 30 4 * * *` UTC (= 10:00 IST) |
| Manual | GitHub → **Actions** → **Daily Corpus Ingest** → **Run workflow** |

The workflow fetches live Groww pages, rebuilds the ChromaDB index, uploads a `chroma-index-*` artifact (14 days), and commits `data/corpus_registry.json` + `data/processed/schemes.json` when timestamps change.

Local scheduler entrypoint: `python scheduler/daily_ingest_job.py`

## Frontend

The Stitch chat UI lives in `frontend/` and calls this API via `VITE_API_BASE_URL`.

See [implementation.md](../Docs%20folder/implementation.md) Phase 2 (backend) and Phase 4 (frontend).

**Disclaimer:** Facts-only. No investment advice.
