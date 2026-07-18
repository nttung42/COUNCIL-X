"""Endpoint tạo yêu cầu thẩm định + stream tiến độ (SSE).

- ``POST /api/appraisal-requests`` : tạo CaseSession, spawn pipeline nền, trả 202 NGAY.
- ``GET  /api/cases/{id}/stream``  : SSE, đẩy TraceEvent + active_tab; đóng khi terminal.
"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.api._common import require_case
from app.orchestrator import event_bus
from app.orchestrator.case_store import get_store
from app.orchestrator.paa_orchestrator import (
    run_appraisal_pipeline,
    tab_for_component,
)
from app.schemas import AppraisalRequestAccepted, PropertyAppraisalRequest

router = APIRouter(tags=["appraisal"])

# Giữ tham chiếu task nền để không bị GC (RUF006).
_BACKGROUND_TASKS: set[asyncio.Task] = set()


@router.post(
    "/api/appraisal-requests",
    status_code=202,
    response_model=AppraisalRequestAccepted,
)
async def create_appraisal_request(payload: PropertyAppraisalRequest):
    store = get_store()
    request_dict = payload.model_dump(mode="json")
    case = store.create_case(request_dict)

    task = asyncio.create_task(run_appraisal_pipeline(case["id"], store))
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)

    return AppraisalRequestAccepted(
        case_id=case["id"], request_id=case["request_id"], status="processing"
    )


def _sse(event_name: str, data: dict) -> str:
    return f"event: {event_name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/api/cases/{case_id}/stream")
async def stream_case(case_id: str, request: Request):
    case = require_case(case_id)  # 404 nếu không tồn tại

    async def gen():
        # (1) replay các TraceEvent đã có (client mở stream muộn vẫn thấy đủ).
        store = get_store()
        for e in store.get_trace_events(case_id):
            yield _sse("step_update", {
                "step_name": e.get("step_name"),
                "active_tab": tab_for_component(e.get("component")),
                "chat_message": e.get("output_summary") or e.get("step_name"),
                "t_offset_seconds": e.get("t_offset_seconds"),
                "status": (store.get_case(case_id) or {}).get("status", "processing"),
            })

        status = (store.get_case(case_id) or {}).get("status", "processing")
        if status in event_bus.TERMINAL_STATUSES:
            yield _sse("done", {"status": status})
            return

        # (2) subscribe event mới.
        queue = event_bus.subscribe(case_id)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    evt = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"  # comment giữ kết nối
                    continue
                yield _sse("step_update", {
                    "step_name": evt.get("step_name"),
                    "active_tab": evt.get("active_tab", tab_for_component(evt.get("component"))),
                    "chat_message": evt.get("chat_message"),
                    "t_offset_seconds": evt.get("t_offset_seconds"),
                    "status": evt.get("status", "processing"),
                })
                if evt.get("status") in event_bus.TERMINAL_STATUSES:
                    yield _sse("done", {"status": evt.get("status")})
                    break
        finally:
            event_bus.unsubscribe(case_id, queue)

    return StreamingResponse(gen(), media_type="text/event-stream")
