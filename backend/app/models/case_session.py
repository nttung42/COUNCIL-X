"""CaseSession ORM model — bảng lưu 1 hồ sơ thẩm định (data-model.md §10).

NOTE (Orchestrator & API agent): Foundational phase chưa tạo model này nên agent
Orchestrator & API tạo, dùng chung ``Base`` từ ``app.db.session``. Dùng kiểu cột
khả chuyển (``GUID`` + ``JSON``) để ``create_all`` chạy cả trên Postgres lẫn SQLite.

State transitions: ``processing → completed`` | ``processing → cancelled`` (không
có transition ngược — data-model.md §10).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models._types import GUID


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CaseSession(Base):
    __tablename__ = "case_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    trace_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    # processing | completed | cancelled
    status: Mapped[str] = mapped_column(Text, nullable=False, default="processing")

    subject_property_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    loan_context_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    lookup_result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    valuation_result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    checklist_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    report_draft_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    chat_history_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    requires_human_verification: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    trace_events: Mapped[list] = relationship(
        "TraceEvent",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="TraceEvent.t_offset_seconds",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CaseSession request_id={self.request_id!r} status={self.status!r}>"
