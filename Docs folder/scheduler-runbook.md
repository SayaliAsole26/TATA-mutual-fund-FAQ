# Scheduler runbook — Daily corpus ingest (10:00 IST)

## Schedule

| Item | Value |
|------|--------|
| Workflow | `.github/workflows/daily-ingest.yml` |
| Cron | `30 4 * * *` UTC = **10:00 Asia/Kolkata (IST)** |
| Schemes | 15 Tata Mutual Fund Groww pages |
| Artifacts | `chroma-index-<run_id>` (14 days), `ingest-summary-<run_id>` (30 days) |

## What the job does

1. Fetch live Groww pages for all 15 schemes
2. Parse, chunk, and rebuild BGE vector index
3. Upload Chroma artifact to GitHub Actions
4. Commit updated `corpus_registry.json`, `schemes.json`, and `*_chunks.json`

## Success criteria

- Workflow status **green**
- `ingest-result.json` shows `"status": "ok"`
- `last_ingested_at` timestamps updated in `data/corpus_registry.json`
- `/api/health` reports `"corpus": { "status": "fresh" }` (age &lt; 26 hours)

## Manual trigger

GitHub → **Actions** → **Daily Corpus Ingest** → **Run workflow**

Optional: set **Skip BGE-large vector index rebuild** only when debugging fetch/parse (not for production).

## On ingestion failure

1. Open the failed run → read **Run ingestion pipeline** and **Verify ingest status** logs
2. Check for Groww rate limits, HTTP timeouts, or parser errors for a specific scheme
3. Re-run workflow manually (it retries failed schemes once internally)
4. If index is stale on Railway, either:
   - Wait for next scheduled run, or
   - `POST /api/ingest` with `X-Admin-Key`, or
   - Redeploy Railway (auto embed-only bootstrap from bundled chunks)

## Staleness alerting

`/api/health` includes:

```json
"corpus": {
  "status": "fresh|stale",
  "age_hours": 12.5,
  "stale_after_hours": 26
}
```

When `status` is **stale** or `issues` contains `corpus_stale`, investigate the last GitHub Actions run.

## Log retention

| Location | Retention |
|----------|-----------|
| GitHub Actions run logs | 90 days (repo settings) |
| Chroma artifact | 14 days |
| Ingest summary JSON artifact | 30 days |

## Production Railway note

Railway does **not** run the scheduler — it serves the API only. Freshness depends on GitHub Actions commits + optional manual `POST /api/ingest`. For production index persistence, attach a Railway volume at `/app/data/index` or restore from the latest `chroma-index-*` artifact.
