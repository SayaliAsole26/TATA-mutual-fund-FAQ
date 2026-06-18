# Mutual Fund FAQ Assistant — production API image
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch keeps the image smaller for sentence-transformers / BGE
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend /app/backend
COPY data/corpus_registry.json /app/data/corpus_registry.json
COPY data/processed/schemes.json /app/data/processed/schemes.json
COPY data/processed/ /app/data/processed/
RUN mkdir -p /app/data/index /app/data/raw

WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    DATA_DIR=/app/data \
    PREFER_LOCAL_SNAPSHOTS=false \
    AUTO_INGEST_ON_STARTUP=true \
    EMBEDDING_MODEL_LARGE=BAAI/bge-small-en-v1.5 \
    EMBED_BATCH_SIZE=8

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=15s --start-period=180s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT:-8000}/api/health" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
