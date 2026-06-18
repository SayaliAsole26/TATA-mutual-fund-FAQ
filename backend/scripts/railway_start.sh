#!/bin/sh
# Railway / container entry: build vector index if missing, then start API.
set -e

cd /app/backend

python - <<'PY'
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from app.ingestion.embed_index import stats

index = stats()
if index.get("status") == "ok":
    print("Vector index present:", index)
    sys.exit(0)

print("Vector index missing or empty — running one-time ingest (this may take several minutes)...")
result = subprocess.run(
    [sys.executable, "scripts/ingest_corpus.py", "--force-live"],
    cwd=Path.cwd(),
    check=False,
)
if result.returncode != 0:
    print("WARNING: ingest failed; API will start in degraded mode", file=sys.stderr)
PY

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
