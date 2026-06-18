# Mutual Fund FAQ Assistant

Facts-only RAG chat assistant for **15 Tata Mutual Fund schemes** listed on Groww.

> **Facts-only. No investment advice.**

## Architecture

```
Groww pages ──► daily ingest (10:00 IST) ──► ChromaDB index
                                              │
User (Vercel UI) ──► FastAPI (Railway) ──► retriever ──► Groq LLM ──► formatted answer
```

| Layer | Stack |
|-------|--------|
| Frontend | Vite + React + Tailwind (Stitch Obsidian theme) |
| Backend | FastAPI, Python 3.12 |
| Embeddings | BGE (local, sentence-transformers) |
| Vector store | ChromaDB at `data/index/` |
| LLM | Groq (`llama-3.1-8b-instant`) |
| Scheduler | GitHub Actions `.github/workflows/daily-ingest.yml` |
| Deploy | Railway (API) + Vercel (UI) |

## Corpus — 15 Tata schemes

All schemes are Tata Mutual Fund direct growth plans on Groww. See `data/corpus_registry.json` for IDs and URLs.

Examples: Tata ELSS, Tata Flexi Cap, Tata Arbitrage, Tata BSE Sensex Index, Tata Silver ETF FoF, Tata Small Cap, …

## Quick start (local)

### 1. Backend

```bash
cd backend
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
cp .env.example .env          # add GROQ_API_KEY
python scripts/ingest_corpus.py --embed-only   # if data/index/ empty
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env          # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Open http://localhost:5173

## Environment variables

| Variable | Where | Purpose |
|----------|-------|---------|
| `GROQ_API_KEY` | Railway | LLM generation (**not** Vercel) |
| `CORS_ORIGINS` | Railway | Vercel URL, no trailing slash |
| `VITE_API_BASE_URL` | Vercel | Railway API URL (`https://…`) |
| `INGEST_API_KEY` | Railway | Optional `POST /api/ingest` |
| `CHAT_RATE_LIMIT_PER_MINUTE` | Railway | Default 30 |
| `CORPUS_STALE_HOURS` | Railway | Alert threshold, default 26 |

See `backend/.env.example` for the full list.

## Manual ingestion

```bash
cd backend
python scripts/ingest_corpus.py --force-live    # fetch Groww + rebuild index
python scripts/ingest_corpus.py --embed-only    # rebuild from bundled chunks only
```

Admin API (production):

```bash
curl -X POST https://<railway>/api/ingest -H "X-Admin-Key: $INGEST_API_KEY"
```

## Tests

```bash
cd backend
pytest -q                       # all tests
pytest tests/test_golden_set.py # factual + refusal golden set (needs index)
pytest tests/test_guardrails.py # PII, advisory, output validation
```

CI runs on every push via `.github/workflows/ci.yml` (embed-only index + full pytest).

## Deployment

| Service | Platform | Config |
|---------|----------|--------|
| API | Railway | Root `Dockerfile`, see `railway.toml` |
| UI | Vercel | Root `vercel.json`, `VITE_API_BASE_URL` |
| Daily ingest | GitHub Actions | 10:00 IST cron |

Detailed notes: `Docs folder/railway-deploy.md`, `Docs folder/scheduler-runbook.md`

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Index, LLM, corpus freshness |
| `GET` | `/api/schemes` | 15 scheme list |
| `POST` | `/api/chat` | Facts-only Q&A (rate limited) |
| `POST` | `/api/ingest` | Admin re-index |

## Known limitations

- **Groww-only corpus** — refuses other AMCs and generic advice
- **Facts-only** — no performance predictions, comparisons, or personalised advice
- **English queries** — optimised for the 15 registered scheme names
- **Ephemeral index on Railway** — rebuilt on deploy from bundled chunks (~3–10 min); use a volume for persistence
- **CPU embeddings** — first query after cold start may be slower while BGE loads

## Disclaimer

This assistant shares verified factual information from official scheme sources. It does **not** provide investment advice, recommendations, or performance forecasts. Mutual fund investments are subject to market risks. Read all scheme-related documents carefully.

Educational links: [AMFI Investor Corner](https://www.amfiindia.com/investor-corner) · [SEBI Investor Education](https://investor.sebi.gov.in/)

## Documentation

- [implementation.md](Docs%20folder/implementation.md) — phased build plan
- [architecture.md](Docs%20folder/architecture.md) — system design
- [backend/README.md](backend/README.md) — API details
- [frontend/README.md](frontend/README.md) — UI setup
