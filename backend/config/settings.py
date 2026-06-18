"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_ROOT / ".env", REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Groq LLM
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL")
    groq_temperature: float = Field(default=0.1, alias="GROQ_TEMPERATURE")

    # API
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )
    ingest_api_key: str = Field(default="", alias="INGEST_API_KEY")
    auto_ingest_on_startup: bool = Field(default=False, alias="AUTO_INGEST_ON_STARTUP")

    embed_batch_size: int = Field(default=16, alias="EMBED_BATCH_SIZE")

    # Retrieval
    retrieval_max_distance: float = Field(default=0.55, alias="RETRIEVAL_MAX_DISTANCE")

    # BGE embeddings
    embedding_model_large: str = Field(
        default="BAAI/bge-large-en-v1.5", alias="EMBEDDING_MODEL_LARGE"
    )
    embedding_model_small: str = Field(
        default="BAAI/bge-small-en-v1.5", alias="EMBEDDING_MODEL_SMALL"
    )

    # Scheduler
    timezone: str = Field(default="Asia/Kolkata", alias="TIMEZONE")
    ingest_cron: str = Field(default="0 10 * * *", alias="INGEST_CRON")

    # Fetcher
    fetch_delay_seconds: float = Field(default=1.5, alias="FETCH_DELAY_SECONDS")
    fetch_timeout_seconds: float = Field(default=30.0, alias="FETCH_TIMEOUT_SECONDS")
    prefer_local_snapshots: bool = Field(default=True, alias="PREFER_LOCAL_SNAPSHOTS")
    groww_user_agent: str = Field(
        default="MutualFundFAQAssistant/1.0 (+https://github.com; educational corpus ingestion)",
        alias="GROWW_USER_AGENT",
    )

    # Paths (data/ lives at repo root, shared with frontend docs)
    data_dir: Path = Field(default=REPO_ROOT / "data", alias="DATA_DIR")
    corpus_registry_path: Path = Field(
        default=REPO_ROOT / "data" / "corpus_registry.json",
        alias="CORPUS_REGISTRY_PATH",
    )

    @property
    def raw_dir(self) -> Path:
        """Fetched Groww page snapshots (markdown / text)."""
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        """Parsed sections, structured fields, and chunk JSON for manual review."""
        return self.data_dir / "processed"

    @property
    def index_dir(self) -> Path:
        """Vector store / embedding index for RAG retrieval."""
        return self.data_dir / "index"

    @property
    def vector_store_dir(self) -> Path:
        """Alias for index_dir (backward compatibility)."""
        return self.index_dir

    @property
    def schemes_metadata_path(self) -> Path:
        return self.processed_dir / "schemes.json"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
