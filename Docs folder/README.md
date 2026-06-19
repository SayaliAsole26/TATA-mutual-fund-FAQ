# Mutual Fund FAQ Assistant — Project README

**Facts-only RAG chat assistant for Tata Mutual Fund schemes on Groww.**

> Facts-only. No investment advice.

## Live deployment

| Service | URL |
|---------|-----|
| Chat UI | https://tata-mutual-fund-faq.vercel.app |
| API | https://tata-mutual-fund-faq-production.up.railway.app |
| Source code | https://github.com/SayaliAsole26/TATA-mutual-fund-FAQ |

---

## Scope

### AMC

**Tata Mutual Fund only.** The assistant does not answer questions about HDFC, SBI, ICICI, or any other asset management company.

### Schemes (15)

Fixed corpus of **15 Tata Mutual Fund direct growth / direct plan** schemes published on Groww. See the full URL list in [source-list.md](./source-list.md) or [source-list.csv](./source-list.csv).

Examples:

- Tata ELSS Fund Direct Growth  
- Tata Flexi Cap Fund Direct Growth  
- Tata Arbitrage Fund Direct Growth  
- Tata Silver ETF FoF Direct Growth  
- Tata BSE Sensex Index Direct  
- … (10 more — see source list)

### What the assistant answers

Objective, verifiable scheme facts from ingested Groww pages, such as:

- Expense ratio  
- Minimum SIP / lumpsum  
- Exit load  
- Lock-in period (e.g. ELSS)  
- Benchmark  
- Fund managers  
- Riskometer / category  

### What it refuses

- Investment advice or recommendations (“Should I invest…?”)  
- Fund comparisons (“Which is better…?”)  
- Performance predictions or return forecasts  
- Personal data (PAN, Aadhaar, account numbers)  
- Questions about schemes outside the 15-scheme corpus  

---

## Setup (local)

### Prerequisites

- Python 3.12+  
- Node.js 18+  
- [Groq API key](https://console.groq.com) (`GROQ_API_KEY`)  

### 1. Backend

```bash
cd backend
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
cp .env.example .env          # add GROQ_API_KEY
python scripts/ingest_corpus.py --embed-only   # if data/index/ is empty
uvicorn app.main:app --reload --port 8000
```

- Health: http://localhost:8000/api/health  
- API docs: http://localhost:8000/docs  

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env          # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Open http://localhost:5173

### 3. Tests

```bash
cd backend
pytest -q
```

---

## Production setup

### Railway (API)

| Variable | Required | Example |
|----------|----------|---------|
| `GROQ_API_KEY` | Yes | `gsk_…` from Groq Console |
| `CORS_ORIGINS` | Yes | `https://tata-mutual-fund-faq.vercel.app` |
| `CORS_ORIGIN_REGEX` | No | `https://.*\.vercel\.app` (default) |

See [railway-deploy.md](./railway-deploy.md).

### Vercel (UI)

| Variable | Required | Example |
|----------|----------|---------|
| `VITE_API_BASE_URL` | Yes | `https://tata-mutual-fund-faq-production.up.railway.app` |

Use **https**, no trailing slash.

---

## Known limitations

| Limitation | Detail |
|------------|--------|
| **Groww-only corpus** | Facts come from 15 Groww scheme pages; not AMC official PDFs or other platforms |
| **Tata AMC only** | No other fund houses in scope |
| **Facts-only** | No advice, opinions, comparisons, or personalised recommendations |
| **English queries** | Optimised for English scheme names and factual questions |
| **Corpus freshness** | Updated daily at 10:00 IST; footer shows last ingested date per scheme |
| **Rate limit** | 30 chat requests per minute per IP (production) |
| **LLM dependency** | Vector-backed answers use Groq; structured fields may bypass LLM |
| **Embedding model** | BGE-large (`BAAI/bge-large-en-v1.5`); index must match runtime model |
| **No user accounts** | Chat sessions are browser-local only; no PII stored server-side |

---

## Documentation index

| Document | Description |
|----------|-------------|
| [end-to-end-guide.md](./end-to-end-guide.md) | Full architecture, API, deployment |
| [source-list.md](./source-list.md) / [source-list.csv](./source-list.csv) | Corpus URLs |
| [sample-qa.md](./sample-qa.md) | Example queries and answers |
| [disclaimer.md](./disclaimer.md) | UI disclaimer text |
| [implementation.md](./implementation.md) | Phased build plan |
| [architecture.md](./architecture.md) | System design |
| [scheduler-runbook.md](./scheduler-runbook.md) | Daily ingest operations |

---

## Disclaimer

Facts-only. No investment advice. Mutual fund investments are subject to market risks. Read all scheme related documents carefully.

See [disclaimer.md](./disclaimer.md) for the exact UI snippet.
