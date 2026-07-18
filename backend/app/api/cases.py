"""Endpoint đọc/quản lý case: GET chi tiết, list, toggle checklist, huỷ."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.api._common import build_case_response, require_case
from app.errors import PaaError
from app.orchestrator.case_store import get_store
from app.schemas import CaseSummary, ChecklistToggleIn

router = APIRouter(tags=["cases"])


@router.get("/api/cases")
async def list_cases(
    status: Optional[str] = Query(None, pattern="^(processing|completed|cancelled)$"),
) -> list[CaseSummary]:
    store = get_store()
    out = []
    for c in store.list_cases(status=status):
        sp = c.get("subject_property_json") or {}
        out.append(CaseSummary(
            case_id=c.get("id"),
            address=sp.get("address", ""),
            status=c.get("status"),
            updated_at=c.get("updated_at"),
        ))
    return out


@router.get("/api/cases/{case_id}")
async def get_case(case_id: str) -> dict:
    return build_case_response(require_case(case_id))


@router.patch("/api/cases/{case_id}/checklist/{item_id}")
async def toggle_checklist(case_id: str, item_id: str, body: ChecklistToggleIn) -> dict:
    require_case(case_id)  # 404 nếu case không tồn tại
    store = get_store()
    item = store.update_checklist_item(case_id, item_id, body.is_checked)
    if item is None:
        raise PaaError(
            "not_found",
            f"Không tìm thấy mục checklist {item_id} trong case {case_id}.",
            status_code=404,
        )
    return item


@router.post("/api/cases/{case_id}/cancel")
async def cancel_case(case_id: str) -> dict:
    case = require_case(case_id)
    if case.get("status") == "completed":
        raise PaaError(
            "conflict",
            "Không thể huỷ hồ sơ đã hoàn tất (completed).",
            status_code=409,
        )
    store = get_store()
    updated = store.set_status(case_id, "cancelled")
    return {"case_id": case_id, "status": updated.get("status")}
