"""Application configuration (minimal Foundational stub).

Đọc cấu hình từ biến môi trường / `.env` qua pydantic-settings. KHÔNG hardcode
API key / base_url / model name (Nguyên tắc IV — Technical Context của plan.md).

NOTE (Advisory & RAG agent): file này lẽ ra thuộc Foundational phase nhưng chưa
được agent nào tạo, nên agent Advisory & RAG tạo bản TỐI THIỂU đủ dùng cho RAG.
Agent Orchestrator & API có thể mở rộng thêm field (VD: các cấu hình ADK) — chỉ
THÊM field mới, không đổi tên/xoá field đã có.
"""

from __future__ import annotations

try:
    # pydantic-settings v2 (Pydantic v2)
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )

        # --- LLM / Embedding (OpenAI-compatible qua custom base_url) ---
        llm_base_url: str = "http://localhost:8000/v1"
        llm_api_key: str = "sk-placeholder-not-set"
        llm_model: str = "gpt-4o-mini"
        embedding_model: str = "text-embedding-3-small"
        # Số chiều vector của embedding_model (text-embedding-3-small = 1536).
        # Đổi theo model thật khi cấu hình .env.
        embedding_dim: int = 1536

        # --- Database (PostgreSQL + pgvector) ---
        # Dùng driver sync (psycopg / psycopg2) cho script ingest + query RAG.
        database_url: str = (
            "postgresql+psycopg://paa:paa@localhost:5432/paa"
        )

except ImportError:  # pragma: no cover - fallback nếu chưa cài pydantic-settings
    import os

    class Settings:  # type: ignore[no-redef]
        def __init__(self) -> None:
            self.llm_base_url = os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")
            self.llm_api_key = os.getenv("LLM_API_KEY", "sk-placeholder-not-set")
            self.llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
            self.embedding_model = os.getenv(
                "EMBEDDING_MODEL", "text-embedding-3-small"
            )
            self.embedding_dim = int(os.getenv("EMBEDDING_DIM", "1536"))
            self.database_url = os.getenv(
                "DATABASE_URL", "postgresql+psycopg://paa:paa@localhost:5432/paa"
            )


settings = Settings()
