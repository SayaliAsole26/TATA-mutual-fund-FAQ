# API Documentation — Mutual Fund FAQ Assistant

**Version:** 0.3.0  
**Base URL (production):** `https://tata-mutual-fund-faq-production.up.railway.app`  
**Interactive docs:** [https://tata-mutual-fund-faq-production.up.railway.app/docs](https://tata-mutual-fund-faq-production.up.railway.app/docs)  
**OpenAPI JSON:** [https://tata-mutual-fund-faq-production.up.railway.app/openapi.json](https://tata-mutual-fund-faq-production.up.railway.app/openapi.json)

Facts-only RAG API for **15 Tata Mutual Fund** schemes on Groww. No investment advice.

---

## Quick reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | [`/`](https://tata-mutual-fund-faq-production.up.railway.app/) | None | Service info + health snapshot |
| `GET` | [`/api/health`](https://tata-mutual-fund-faq-production.up.railway.app/api/health) | None | Index, corpus, LLM status |
| `GET` | [`/api/schemes`](https://tata-mutual-fund-faq-production.up.railway.app/api/schemes) | None | List of 15 schemes |
| `POST` | [`/api/chat`](https://tata-mutual-fund-faq-production.up.railway.app/api/chat) | None | Facts-only Q&A (rate limited) |
| `POST` | `/api/ingest` | `X-Admin-Key` | Admin corpus re-index |

---

## Authentication

| Endpoint | Authentication |
|----------|----------------|
| `/api/health`, `/api/schemes`, `/api/chat`, `/` | **None** — public read/chat |
| `/api/ingest` | Header `X-Admin-Key: <INGEST_API_KEY>` (set on Railway) |

No user login or session tokens. Chat rate limiting is by client IP (default **30 requests/minute**).

---

## CORS

Browser calls from the Vercel UI require CORS on Railway:

| Variable | Example |
|----------|---------|
| `CORS_ORIGINS` | `https://tata-mutual-fund-faq.vercel.app` |
| `CORS_ORIGIN_REGEX` | `https://.*\.vercel\.app` (Vercel previews) |

Allowed methods: all. Allowed headers: all. Credentials: supported.

---

## Endpoints

### GET `/`

Service root — returns health payload plus metadata.

**URL:** [https://tata-mutual-fund-faq-production.up.railway.app/](https://tata-mutual-fund-faq-production.up.railway.app/)

**Response `200 OK`**

```json
{
  "status": "ok",
  "index": { "status": "ok", "chunk_count": 181, "scheme_count": 15 },
  "corpus": { "status": "fresh", "scheme_count": 15 },
  "llm": { "provider": "groq", "configured": true, "model": "llama-3.1-8b-instant" },
  "issues": [],
  "service": "mutual-fund-faq-assistant",
  "docs": "/docs",
  "health": "/api/health"
}
```

---

### GET `/api/health`

Operational health for monitoring and frontend readiness checks.

**URL:** [https://tata-mutual-fund-faq-production.up.railway.app/api/health](https://tata-mutual-fund-faq-production.up.railway.app/api/health)

**Response `200 OK`**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `ok` or `degraded` |
| `issues` | string[] | e.g. `index`, `groq_api_key`, `corpus_stale` |
| `index.status` | string | `ok` · `empty` · `missing_collection` |
| `index.chunk_count` | number | Vector count (expect **181**) |
| `index.scheme_count` | number | Scheme count (expect **15**) |
| `index.embedding_model` | string | e.g. `BAAI/bge-large-en-v1.5` |
| `corpus.status` | string | `fresh` or `stale` |
| `corpus.age_hours` | number | Hours since newest ingest |
| `corpus.stale_after_hours` | number | Alert threshold (default **26**) |
| `llm.configured` | boolean | `GROQ_API_KEY` present |
| `llm.model` | string | Groq model name |
| `ingest` | object | Optional — background index bootstrap state |

**Example `ingest` object (when index is building)**

```json
{
  "status": "running",
  "mode": "embed_only",
  "started_at": "2027-06-18T21:30:14.476493+00:00",
  "finished_at": null,
  "exit_code": null,
  "error": null
}
```

**Example request**

```bash
curl https://tata-mutual-fund-faq-production.up.railway.app/api/health
```

---

### GET `/api/schemes`

Returns all schemes in the fixed corpus.

**URL:** [https://tata-mutual-fund-faq-production.up.railway.app/api/schemes](https://tata-mutual-fund-faq-production.up.railway.app/api/schemes)

**Response `200 OK`**

```json
{
  "amc": "Tata Mutual Fund",
  "schemes": [
    {
      "scheme_id": "tata-elss-fund-direct-growth",
      "scheme_name": "Tata ELSS Fund Direct Growth",
      "source_url": "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
      "category": "ELSS"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `amc` | string | Always `Tata Mutual Fund` |
| `schemes[].scheme_id` | string | Stable slug used in retrieval |
| `schemes[].scheme_name` | string | Display name |
| `schemes[].source_url` | string | Groww scheme page (HTTPS) |
| `schemes[].category` | string | Fund category |

**Example request**

```bash
curl https://tata-mutual-fund-faq-production.up.railway.app/api/schemes
```

---

### POST `/api/chat`

Main chat endpoint. Accepts a natural-language question about one of the 15 Tata schemes.

**URL:** [https://tata-mutual-fund-faq-production.up.railway.app/api/chat](https://tata-mutual-fund-faq-production.up.railway.app/api/chat)

**Headers**

| Header | Required | Value |
|--------|----------|-------|
| `Content-Type` | Yes | `application/json` |

**Request body**

```json
{
  "message": "What is the minimum SIP for Tata ELSS?"
}
```

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `message` | string | 1–2000 chars | User question |

**Rate limit:** 30 requests per minute per IP (configurable via `CHAT_RATE_LIMIT_PER_MINUTE`).  
**Response on limit:** `429 Too Many Requests`

```json
{
  "type": "error",
  "message": "Too many requests. Please wait a minute and try again."
}
```

---

#### Response type: `answer`

Factual answer from corpus (structured field or vector retrieval + optional LLM).

**HTTP `200 OK`**

```json
{
  "type": "answer",
  "answer": "Minimum SIP: ₹500.\n\nSource: https://groww.in/mutual-funds/tata-elss-fund-direct-growth\n\nLast updated from sources: 18 Jun 2027",
  "scheme_id": "tata-elss-fund-direct-growth",
  "scheme_name": "Tata ELSS Fund Direct Growth",
  "source_url": "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
  "last_updated": "2027-06-18T19:37:32.828925+00:00",
  "sections_used": ["min_sip"],
  "retrieval_source": "structured"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"answer"` | Response discriminator |
| `answer` | string | Formatted body + `Source:` + `Last updated from sources:` |
| `scheme_id` | string | Resolved scheme slug |
| `scheme_name` | string | Human-readable scheme name |
| `source_url` | string | Primary Groww citation (HTTPS) |
| `last_updated` | string \| null | ISO timestamp from corpus |
| `sections_used` | string[] | e.g. `expense_ratio`, `exit_load`, `min_sip` |
| `retrieval_source` | string | `structured` or `vector` |

**Example request**

```bash
curl -X POST https://tata-mutual-fund-faq-production.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What is the minimum SIP for Tata ELSS?\"}"
```

---

#### Response type: `clarification`

Scheme could not be identified from the message.

**HTTP `200 OK`**

```json
{
  "type": "clarification",
  "message": "Which Tata Mutual Fund scheme do you mean? For example: Tata Small Cap Fund Direct Growth, Tata Digital India Fund Direct Growth, …",
  "schemes": ["tata-small-cap-fund-direct-growth", "tata-digital-india-fund-direct-growth"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"clarification"` | Response discriminator |
| `message` | string | Prompt asking user to pick a scheme |
| `schemes` | string[] | All 15 `scheme_id` values |

---

#### Response type: `refusal`

Guardrail blocked the query (advice, comparison, PII, etc.).

**HTTP `200 OK`**

```json
{
  "type": "refusal",
  "reason": "advisory",
  "answer": "I am a facts-only assistant and cannot provide investment advice, recommendations, or opinions. For general mutual fund education, please visit the AMFI Investor Corner.\n\nSource: https://www.amfiindia.com/investor-corner\n\nLast updated from sources: 18 Jun 2027",
  "source_url": "https://www.amfiindia.com/investor-corner",
  "scheme_name": "Tata Small Cap Fund Direct Growth"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"refusal"` | Response discriminator |
| `reason` | string | Refusal category (see table below) |
| `answer` | string | Formatted refusal with source |
| `source_url` | string | AMFI / SEBI / scheme page (HTTPS) |
| `scheme_name` | string \| null | Scheme if resolved before refusal |

**Refusal `reason` values**

| `reason` | Trigger |
|----------|---------|
| `advisory` | Investment advice, recommendations (“Should I invest…?”) |
| `comparative` | Fund comparisons or rankings |
| `pii` | PAN, Aadhaar, phone, account numbers |
| `performance` | Return calculations or performance quotes |
| `out_of_corpus` | Non-Tata AMC or unknown scheme |
| `out_of_scope` | General out-of-scope queries |

**Example request (refusal)**

```bash
curl -X POST https://tata-mutual-fund-faq-production.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Should I invest in Tata Small Cap Fund?\"}"
```

---

#### Response type: `error`

Application-level error (empty message, index not ready, etc.).

**HTTP `200 OK`** (in-body error) or **`429`** (rate limit)

```json
{
  "type": "error",
  "message": "Corpus not indexed yet. Please try again after ingestion completes."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"error"` | Response discriminator |
| `message` | string | Human-readable error |

**Common error messages**

| Message | Cause |
|---------|-------|
| `Please enter a question about one of the 15 Tata Mutual Fund schemes.` | Empty `message` |
| `Corpus not indexed yet. Please try again after ingestion completes.` | Chroma index empty |
| `Too many requests. Please wait a minute and try again.` | Rate limit (`429`) |

---

### POST `/api/ingest`

Admin-only trigger for full live corpus re-index (fetch Groww → parse → chunk → embed).

**URL:** `https://tata-mutual-fund-faq-production.up.railway.app/api/ingest`

**Headers**

| Header | Required | Value |
|--------|----------|-------|
| `X-Admin-Key` | Yes | Value of Railway env `INGEST_API_KEY` |

**Request body:** none

**Response `200 OK`**

```json
{
  "status": "ok",
  "message": "Corpus ingestion completed"
}
```

**Error responses**

| HTTP | Detail | Cause |
|------|--------|-------|
| `403` | Invalid or missing admin key | Wrong/missing `X-Admin-Key` |
| `503` | Ingest API is not configured | `INGEST_API_KEY` not set on Railway |
| `500` | Ingestion failed | Subprocess error during ingest |

**Example request**

```bash
curl -X POST https://tata-mutual-fund-faq-production.up.railway.app/api/ingest \
  -H "X-Admin-Key: YOUR_INGEST_API_KEY"
```

> **Note:** This can take 15–45 minutes on Railway (live fetch + BGE embed). Prefer scheduled [GitHub Actions ingest](https://github.com/SayaliAsole26/TATA-mutual-fund-FAQ/actions/workflows/daily-ingest.yml) for routine updates.

---

## HTTP status codes

| Code | When |
|------|------|
| `200` | Success (including chat `refusal` / `clarification` / in-body `error`) |
| `422` | Invalid JSON or validation error (e.g. missing `message`) |
| `429` | Chat rate limit exceeded |
| `403` | Invalid admin key on `/api/ingest` |
| `500` | Server or ingest failure |
| `503` | Ingest API not configured |

**Validation error example (`422`)**

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "message"],
      "msg": "String should have at least 1 character"
    }
  ]
}
```

---

## Answer format convention

All factual and refusal responses use a consistent text layout:

```
<answer body>

Source: https://groww.in/mutual-funds/...

Last updated from sources: 18 Jun 2027
```

The frontend parses this into:

- **Body** — displayed in the Verified Fact card  
- **`source_url`** — “View source” link (JSON field; preferred over parsing)  
- **`last_updated`** — footer date (JSON field; ISO or human-readable)

---

## Frontend integration

The Vercel UI calls the API via `VITE_API_BASE_URL`:

| Environment | Variable value |
|-------------|----------------|
| Production | `https://tata-mutual-fund-faq-production.up.railway.app` |
| Local dev | `http://localhost:8000` |

**Client module:** [`frontend/src/api/client.ts`](../frontend/src/api/client.ts)

| Client function | Endpoint |
|-----------------|----------|
| `getHealth()` | `GET /api/health` |
| `getSchemes()` | `GET /api/schemes` |
| `postChat(message)` | `POST /api/chat` |

**Production UI:** [https://tata-mutual-fund-faq.vercel.app](https://tata-mutual-fund-faq.vercel.app)

---

## Related documentation

| Document | Link |
|----------|------|
| Project README | [README.md](./README.md) |
| End-to-end guide | [end-to-end-guide.md](./end-to-end-guide.md) |
| Sample Q&A | [sample-qa.md](./sample-qa.md) |
| Corpus sources | [source-list.md](./source-list.md) |
| Railway deploy | [railway-deploy.md](./railway-deploy.md) |
| Backend README | [../backend/README.md](../backend/README.md) |

---

## Disclaimer

This API returns **facts-only** information from ingested Groww scheme pages. It does **not** provide investment advice, recommendations, or performance forecasts.

**Mutual fund investments are subject to market risks. Read all scheme related documents carefully.**
