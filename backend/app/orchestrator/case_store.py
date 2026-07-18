"""Case store — lưu/đọc CaseSession + TraceEvent.

Hai backend, chọn qua ``settings.store_backend``:
- ``"memory"`` (mặc định): dict trong process — chạy được NGAY không cần Postgres
  (đủ cho demo/hackathon single-process, chứng minh wiring pipeline đúng).
- ``"sql"``: SQLAlchemy + Postgres theo data-model.md §10–11 (cần DB chạy +
  ``Base.metadata.create_all`` / migration).

Cả 2 trả về **dict snapshot** đồng nhất để lớp API serialize giống nhau — không lộ
ORM ra ngoài. Mọi method sync (memory tức thời; SQL đủ nhanh cho MVP).
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.config import settings


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_trace_id() -> str:
    return "TRACE-" + uuid.uuid4().hex[:8].upper()


def _empty_case(request: dict) -> dict:
    cid = str(uuid.uuid4())
    now = _utcnow_iso()
    return {
        "id": cid,
        "request_id": request.get("request_id"),
        "trace_id": _new_trace_id(),
        "status": "processing",
        "subject_property_json": request.get("subject_property") or {},
        "loan_context_json": request.get("loan_context"),
        "lookup_result_json": None,
        "valuation_result_json": None,
        "risk_result_json": None,
        "checklist_json": None,
        "report_draft_json": None,
        "chat_history_json": [],
        "requires_human_verification": True,  # Nguyên tắc I — luôn True ở MVP
        "created_at": now,
        "updated_at": now,
    }


# --------------------------------------------------------------------------- #
# In-memory store (mặc định)
# --------------------------------------------------------------------------- #
class InMemoryCaseStore:
    def __init__(self) -> None:
        self._cases: dict[str, dict] = {}
        self._events: dict[str, list[dict]] = {}
        self._lock = threading.RLock()

    def create_case(self, request: dict) -> dict:
        case = _empty_case(request)
        with self._lock:
            self._cases[case["id"]] = case
            self._events[case["id"]] = []
        return dict(case)

    def get_case(self, case_id: str) -> Optional[dict]:
        with self._lock:
            case = self._cases.get(case_id)
            if case is None:
                return None
            snap = dict(case)
            snap["trace_events"] = [dict(e) for e in self._events.get(case_id, [])]
            return snap

    def list_cases(self, status: Optional[str] = None) -> list[dict]:
        with self._lock:
            cases = list(self._cases.values())
        if status:
            cases = [c for c in cases if c["status"] == status]
        cases.sort(key=lambda c: c["updated_at"], reverse=True)
        return [dict(c) for c in cases]

    def update_fields(self, case_id: str, **fields) -> Optional[dict]:
        with self._lock:
            case = self._cases.get(case_id)
            if case is None:
                return None
            case.update(fields)
            case["updated_at"] = _utcnow_iso()
            return dict(case)

    def set_status(self, case_id: str, status: str) -> Optional[dict]:
        return self.update_fields(case_id, status=status)

    def append_chat(self, case_id: str, message: dict) -> Optional[dict]:
        with self._lock:
            case = self._cases.get(case_id)
            if case is None:
                return None
            case.setdefault("chat_history_json", []).append(message)
            case["updated_at"] = _utcnow_iso()
            return dict(case)

    def add_trace_event(
        self,
        case_id: str,
        step_name: str,
        component: str,
        t_offset_seconds: float,
        input_summary: str = "",
        output_summary: str = "",
    ) -> dict:
        event = {
            "id": str(uuid.uuid4()),
            "case_id": case_id,
            "step_name": step_name,
            "component": component,
            "t_offset_seconds": round(float(t_offset_seconds), 3),
            "input_summary": input_summary,
            "output_summary": output_summary,
            "created_at": _utcnow_iso(),
        }
        with self._lock:
            self._events.setdefault(case_id, []).append(event)
        return dict(event)

    def get_trace_events(self, case_id: str) -> list[dict]:
        with self._lock:
            events = list(self._events.get(case_id, []))
        events.sort(key=lambda e: e["t_offset_seconds"])
        return [dict(e) for e in events]

    def update_checklist_item(
        self, case_id: str, item_id: str, is_checked: bool
    ) -> Optional[dict]:
        with self._lock:
            case = self._cases.get(case_id)
            if case is None:
                return None
            checklist = case.get("checklist_json") or []
            for item in checklist:
                if str(item.get("item_id")) == str(item_id):
                    item["is_checked"] = bool(is_checked)
                    case["updated_at"] = _utcnow_iso()
                    return dict(item)
            return None


# --------------------------------------------------------------------------- #
# SQL store (Postgres theo data-model.md) — dùng khi store_backend="sql"
# --------------------------------------------------------------------------- #
class SqlCaseStore:
    """Backend SQLAlchemy. Bọc mọi thao tác trong 1 session ngắn."""

    _COLUMNS = (
        "request_id", "trace_id", "status", "subject_property_json",
        "loan_context_json", "lookup_result_json", "valuation_result_json",
        "risk_result_json", "checklist_json", "report_draft_json",
        "chat_history_json", "requires_human_verification",
    )

    def _session(self):
        from app.db.session import SessionLocal

        return SessionLocal()

    @staticmethod
    def _to_dict(case) -> dict:
        return {
            "id": str(case.id),
            "request_id": case.request_id,
            "trace_id": case.trace_id,
            "status": case.status,
            "subject_property_json": case.subject_property_json,
            "loan_context_json": case.loan_context_json,
            "lookup_result_json": case.lookup_result_json,
            "valuation_result_json": case.valuation_result_json,
            "risk_result_json": case.risk_result_json,
            "checklist_json": case.checklist_json,
            "report_draft_json": case.report_draft_json,
            "chat_history_json": case.chat_history_json or [],
            "requires_human_verification": case.requires_human_verification,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        }

    @staticmethod
    def _event_to_dict(ev) -> dict:
        return {
            "id": str(ev.id),
            "case_id": str(ev.case_id),
            "step_name": ev.step_name,
            "component": ev.component,
            "t_offset_seconds": ev.t_offset_seconds,
            "input_summary": ev.input_summary,
            "output_summary": ev.output_summary,
            "created_at": ev.created_at.isoformat() if ev.created_at else None,
        }

    def create_case(self, request: dict) -> dict:
        from app.models.case_session import CaseSession

        with self._session() as s:
            case = CaseSession(
                request_id=request.get("request_id"),
                trace_id=_new_trace_id(),
                status="processing",
                subject_property_json=request.get("subject_property") or {},
                loan_context_json=request.get("loan_context"),
                chat_history_json=[],
                requires_human_verification=True,
            )
            s.add(case)
            s.commit()
            s.refresh(case)
            return self._to_dict(case)

    def _get(self, s, case_id):
        from app.models.case_session import CaseSession

        try:
            uid = uuid.UUID(str(case_id))
        except ValueError:
            return None
        return s.get(CaseSession, uid)

    def get_case(self, case_id: str) -> Optional[dict]:
        with self._session() as s:
            case = self._get(s, case_id)
            if case is None:
                return None
            snap = self._to_dict(case)
            snap["trace_events"] = [
                self._event_to_dict(e)
                for e in sorted(case.trace_events, key=lambda e: e.t_offset_seconds)
            ]
            return snap

    def list_cases(self, status: Optional[str] = None) -> list[dict]:
        from sqlalchemy import select

        from app.models.case_session import CaseSession

        with self._session() as s:
            stmt = select(CaseSession)
            if status:
                stmt = stmt.where(CaseSession.status == status)
            stmt = stmt.order_by(CaseSession.updated_at.desc())
            return [self._to_dict(c) for c in s.execute(stmt).scalars().all()]

    def update_fields(self, case_id: str, **fields) -> Optional[dict]:
        with self._session() as s:
            case = self._get(s, case_id)
            if case is None:
                return None
            for k, v in fields.items():
                setattr(case, k, v)
            s.commit()
            s.refresh(case)
            return self._to_dict(case)

    def set_status(self, case_id: str, status: str) -> Optional[dict]:
        return self.update_fields(case_id, status=status)

    def append_chat(self, case_id: str, message: dict) -> Optional[dict]:
        from sqlalchemy.orm.attributes import flag_modified

        with self._session() as s:
            case = self._get(s, case_id)
            if case is None:
                return None
            history = list(case.chat_history_json or [])
            history.append(message)
            case.chat_history_json = history
            flag_modified(case, "chat_history_json")
            s.commit()
            s.refresh(case)
            return self._to_dict(case)

    def add_trace_event(
        self,
        case_id: str,
        step_name: str,
        component: str,
        t_offset_seconds: float,
        input_summary: str = "",
        output_summary: str = "",
    ) -> dict:
        from app.models.trace_event import TraceEvent

        with self._session() as s:
            ev = TraceEvent(
                case_id=uuid.UUID(str(case_id)),
                step_name=step_name,
                component=component,
                t_offset_seconds=round(float(t_offset_seconds), 3),
                input_summary=input_summary,
                output_summary=output_summary,
            )
            s.add(ev)
            s.commit()
            s.refresh(ev)
            return self._event_to_dict(ev)

    def get_trace_events(self, case_id: str) -> list[dict]:
        from sqlalchemy import select

        from app.models.trace_event import TraceEvent

        with self._session() as s:
            stmt = (
                select(TraceEvent)
                .where(TraceEvent.case_id == uuid.UUID(str(case_id)))
                .order_by(TraceEvent.t_offset_seconds)
            )
            return [self._event_to_dict(e) for e in s.execute(stmt).scalars().all()]

    def update_checklist_item(
        self, case_id: str, item_id: str, is_checked: bool
    ) -> Optional[dict]:
        from sqlalchemy.orm.attributes import flag_modified

        with self._session() as s:
            case = self._get(s, case_id)
            if case is None:
                return None
            checklist = list(case.checklist_json or [])
            updated = None
            for item in checklist:
                if str(item.get("item_id")) == str(item_id):
                    item["is_checked"] = bool(is_checked)
                    updated = dict(item)
                    break
            if updated is None:
                return None
            case.checklist_json = checklist
            flag_modified(case, "checklist_json")
            s.commit()
            return updated


# --------------------------------------------------------------------------- #
# Singleton selector
# --------------------------------------------------------------------------- #
_store: Optional[object] = None


def get_store():
    """Trả store singleton theo ``settings.store_backend`` ("memory"|"sql")."""
    global _store
    if _store is None:
        backend = (getattr(settings, "store_backend", "memory") or "memory").lower()
        _store = SqlCaseStore() if backend == "sql" else InMemoryCaseStore()
    return _store
