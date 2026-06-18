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
| `GROQ_API_KEY` | **Yes** | `gsk_…` from [console.groq.com](https://console.groq.com) — **backend only (Railway), not Vercel** |
| `GROQ_MODEL` | No | `llama-3.1-8b-instant` |
| `CORS_ORIGINS` | Yes (if using hosted frontend) | `https://your-frontend.up.railway.app` |
| `INGEST_API_KEY` | Optional | For `POST /api/ingest` |
| `AUTO_INGEST_ON_STARTUP` | Auto in Docker | Set `true` in Dockerfile — builds index on first deploy |
| `PREFER_LOCAL_SNAPSHOTS` | Auto in Docker | Set `false` — fetch live from Groww on Railway |
| `PORT` | Auto | Set by Railway |

4. **Vector index:** baked into the Docker image at build time (`embed-only` in `Dockerfile`), so deploys should report `index.status: ok` immediately. `AUTO_INGEST_ON_STARTUP` only runs if the index is missing (e.g. empty volume). **Do not set `EMBEDDING_MODEL_LARGE` on Railway to a different model than the Dockerfile** (`BAAI/bge-small-en-v1.5`) — mismatched models break search. For persistence across redeploys without rebuild, attach a Railway volume at `/app/data/index`.

5. **Redeploy:** Push this commit, or click **Redeploy** in Railway.

## Local Docker test

```bash
docker build -t tata-mf-faq-api .
docker run --rm -p 8000:8000 -e GROQ_API_KEY=your_key tata-mf-faq-api
curl http://localhost:8000/api/health
```

## Frontend

Deploy `frontend/` as a **separate** Railway/Vercel static service, or run locally with `npm run dev`. Set `VITE_API_BASE_URL` to your Railway API URL.
