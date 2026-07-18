"""Kiểu cột SQLAlchemy khả chuyển (Postgres + SQLite).

Dùng cho CaseSession/TraceEvent để ``Base.metadata.create_all`` chạy được cả trên
Postgres thật (data-model.md §10–11) lẫn SQLite fallback (demo/test không cần
Postgres). KbChunk vẫn giữ kiểu Postgres-specific riêng của nó (RAG bắt buộc
pgvector) — module này KHÔNG đụng tới.
"""

from __future__ import annotations

import uuid

from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):
    """UUID khả chuyển: dùng native UUID trên Postgres, CHAR(36) trên SQLite."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID

            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        if dialect.name == "postgresql":
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))
