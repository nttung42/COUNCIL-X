"""TraceEvent ORM model — 1 bước trong pipeline của 1 case (data-model.md §11).

Tab Dashboard của frontend phụ thuộc hoàn toàn vào bảng này (timeline các bước).
``component`` dùng để suy ra ``active_tab`` cho SSE (xem orchestrator).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models._types import GUID


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TraceEvent(Base):
    __tablename__ = "trace_events"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("case_sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    step_name: Mapped[str] = mapped_column(Text, nullable=False)
    component: Mapped[str | None] = mapped_column(Text, nullable=True)
    t_offset_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    case: Mapped["CaseSession"] = relationship(  # noqa: F821
        "CaseSession", back_populates="trace_events"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TraceEvent step={self.step_name!r} t={self.t_offset_seconds}>"
