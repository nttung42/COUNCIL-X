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
# Timeout kết nối nhanh khi Postgres chưa chạy (quick-start path không Docker) —
# fail trong vài giây thay vì để hệ điều hành chờ hết TCP timeout mặc định (có
# thể >10s trên Windows), giữ đúng ngân sách <15s của SC-001. Tham số này CHỈ
# hợp lệ với driver psycopg/psycopg2 (Postgres) — sqlite3 (dùng trong test/dev
# nhẹ, xem docstring module) không nhận `connect_timeout` nên phải áp dụng
# có điều kiện theo dialect, tránh vỡ khả năng chạy trên SQLite.
_connect_args: dict = {}
if settings.database_url.startswith("postgresql"):
    _connect_args["connect_timeout"] = 3

engine = create_engine(
    settings.database_url,
    future=True,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)
