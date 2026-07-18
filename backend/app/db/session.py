"""SQLAlchemy engine / session (minimal Foundational stub).

NOTE (Advisory & RAG agent): tạo bản tối thiểu vì Foundational phase chưa có.
Dùng engine SYNC (đủ cho script ingest và query_knowledge_base — chữ ký hàm sync
theo skill). Agent Orchestrator & API nếu cần async session có thể THÊM
`async_session`/`AsyncSessionLocal` riêng, không đổi `Base`/`SessionLocal` hiện có
để tránh vỡ import của RAG.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# Declarative base dùng chung cho mọi ORM model của backend.
Base = declarative_base()

# `future=True` để dùng API SQLAlchemy 2.0 style.
engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)
