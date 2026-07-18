"""Application configuration for SHB AI."""

from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseModel):
    """LLM provider configuration via OpenRouter."""

    api_key: str = Field(
        default="",
        description="API key for LLM provider",
    )
    model: str = Field(
        default="cx/gpt-5.5",
        description="Chat model id served by the OpenAI-compatible endpoint (LLM_MODEL).",
    )
    vision_model: str = Field(
        default="",
        description=(
            "Vision-capable model id for OCR / scanned-document extraction "
            "(LLM_VISION_MODEL). Falls back to `model` when empty."
        ),
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0-2)",
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        description="Maximum tokens in response",
    )
    top_p: float | None = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter",
    )
    base_url: str = Field(
        default="",
        description="Base URL of the OpenAI-compatible LLM endpoint (LLM_BASE_URL).",
    )
    enable_prompt_cache: bool = Field(
        default=False,
        description="Attach ephemeral cache_control markers (only for providers that support it).",
    )


class Settings(BaseSettings):
    """Application configuration for SHB AI platform."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
        protected_namespaces=("settings_",),
    )

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost/shb"

    # LLM Configuration
    llm: LLMSettings = Field(default_factory=LLMSettings)

    # Embeddings (OpenAI-compatible endpoint; used by RAG features)
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # Speech-to-Text (Whisper)
    whisper_provider: str = "openai"  # openai or local
    whisper_api_key: str = ""
    whisper_model: str = "whisper-1"

    # File Storage
    storage_dir: str = "storage"
    max_file_size_mb: int = 100
    allowed_file_types: list[str] = ["pdf", "docx", "txt", "mp3", "wav", "m4a"]

    # Document parsing (hybrid PDF text/scan handling)
    pdf_scan_char_threshold: int = Field(
        default=50,
        ge=0,
        description="Chars of extractable text per PDF page below which the page is treated as scanned.",
    )
    pdf_scan_doc_fraction: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Fraction of scanned pages at/above which the whole PDF is treated as scanned.",
    )
    pdf_render_dpi: int = Field(
        default=200,
        ge=72,
        le=600,
        description="DPI used when rasterizing scanned PDF pages to images for OCR / vision LLM.",
    )

    # API Authentication
    api_key_header: str = "X-API-Key"
    secret_key: str = "changeme-in-production"

    # Job Queue (Postgres-backed for MVP)
    job_poll_interval_seconds: int = 5
    job_timeout_seconds: int = 3600
    max_concurrent_workers: int = 4

    # Celery Task Queue Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_worker_concurrency: int = 4
    celery_task_soft_limit: int = 3600
    celery_task_hard_limit: int = 3700
    celery_task_max_retries: int = 3

    # Logging
    log_level: str = "INFO"

    # CORS
    cors_origins: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
