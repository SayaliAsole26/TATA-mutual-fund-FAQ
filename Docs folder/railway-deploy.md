# Railway deployment (backend API)

## Why the build failed

Railway auto-deployed on push but the repo had **no `Dockerfile`** and no root `requirements.txt` (Python lives under `backend/`). Nixpacks could not detect a build → **Build image** failed in ~4 seconds.

The failing deploy was triggered by the GitHub Actions ingest commit (`chore(ingest): daily corpus metadata refresh`).

## Fix added

| File | Purpose |
|------|---------|
| `Dockerfile` | Production API image (FastAPI + BGE + ChromaDB) |
| `railway.toml` | Tells Railway to use the Dockerfile |
| `.dockerignore` | Smaller, faster builds |

## Railway setup

1. **Service root:** repository root (default)
2. **Builder:** Dockerfile (from `railway.toml`)
3. **Variables** (Settings → Variables):

| Variable | Required | Example |
|----------|----------|---------|
| `GROQ_API_KEY` | Yes | `gsk_…` |
| `GROQ_MODEL` | No | `llama-3.1-8b-instant` |
| `CORS_ORIGINS` | Yes (if using hosted frontend) | `https://your-frontend.up.railway.app` |
| `INGEST_API_KEY` | Optional | For `POST /api/ingest` |
| `PORT` | Auto | Set by Railway |

4. **Vector index:** `data/index/` is not in git. After first deploy either:
   - Call `POST /api/ingest` with header `X-Admin-Key: <INGEST_API_KEY>`, or
   - Download the `chroma-index-*` artifact from GitHub Actions and attach a Railway volume at `/app/data/index`

5. **Redeploy:** Push this commit, or click **Redeploy** in Railway.

## Local Docker test

```bash
docker build -t tata-mf-faq-api .
docker run --rm -p 8000:8000 -e GROQ_API_KEY=your_key tata-mf-faq-api
curl http://localhost:8000/api/health
```

## Frontend

Deploy `frontend/` as a **separate** Railway/Vercel static service, or run locally with `npm run dev`. Set `VITE_API_BASE_URL` to your Railway API URL.
