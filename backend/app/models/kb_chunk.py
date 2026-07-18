"""KbChunk ORM model — bảng RAG (Postgres + pgvector).

Theo data-model.md §12. NOTE (Advisory & RAG agent): tạo bản TỐI THIỂU vì
Foundational phase chưa có. Agent khác chỉ import, không sửa; nếu thiếu field thì
THÊM field mới (không đổi field có sẵn).

| Column        | Type        | Ghi chú                                            |
|---------------|-------------|----------------------------------------------------|
| id (PK)       | uuid        |                                                    |
| source_doc    | text        | vd. `06-case-cu-tham-khao.md` (dùng làm citation)  |
| chunk_text    | text        |                                                    |
| embedding     | vector(N)   | N = settings.embedding_dim                         |
| metadata_json | jsonb       | {doc_type, property_type?}                         |
"""

from __future__ import annotations

import uuid

from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.db.session import Base

try:
    from pgvector.sqlalchemy import Vector

    _EMBEDDING_TYPE = Vector(settings.embedding_dim)
except ImportError:  # pragma: no cover - pgvector chưa cài (chỉ chặn chạy, không chặn import test khác)
    _EMBEDDING_TYPE = None  # type: ignore[assignment]


class KbChunk(Base):
    __tablename__ = "kb_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_doc: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    # embedding có thể None nếu pgvector chưa cài (chỉ xảy ra khi chưa setup DB).
    if _EMBEDDING_TYPE is not None:
        embedding: Mapped[list[float]] = mapped_column(_EMBEDDING_TYPE, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<KbChunk source_doc={self.source_doc!r} id={self.id}>"
