"""Helper dùng chung cho các router — build response từ case snapshot.

Giữ nguyên field ``confidence``/``source_type``/``verified`` từ tool gốc (Nguyên
tắc chung contracts/appraisal-api.md): response chỉ ánh xạ tên field cấp cao, KHÔNG
lược bỏ field con của envelope/valuation/risk.
"""

from __future__ import annotations

from app.errors import PaaError
from app.orchestrator.case_store import get_store


def require_case(case_id: str) -> dict:
    """Trả case snapshot đầy đủ (kèm trace_events) hoặc raise 404."""
    case = get_store().get_case(case_id)
    if case is None:
        raise PaaError("not_found", f"Không tìm thấy case {case_id}.", status_code=404)
    return case


def build_case_response(case: dict) -> dict:
    """Map case snapshot -> AppraisalReport mở rộng (contracts mục 3)."""
    trace_events = [
        {
            "step_name": e.get("step_name"),
            "component": e.get("component"),
            "t_offset_seconds": e.get("t_offset_seconds"),
            "input_summary": e.get("input_summary"),
            "output_summary": e.get("output_summary"),
        }
        for e in sorted(
            case.get("trace_events") or [],
            key=lambda e: e.get("t_offset_seconds", 0.0),
        )
    ]
    return {
        "case_id": case.get("id"),
        "request_id": case.get("request_id"),
        "status": case.get("status"),
        "subject_property": case.get("subject_property_json"),
        "loan_context": case.get("loan_context_json"),
        "lookup_result": case.get("lookup_result_json"),
        "valuation": case.get("valuation_result_json"),
        "asset_risk": case.get("risk_result_json"),
        "checklist": case.get("checklist_json"),
        "draft_report": case.get("report_draft_json"),
        "chat_history": case.get("chat_history_json") or [],
        "requires_human_verification": case.get("requires_human_verification", True),
        "trace_id": case.get("trace_id"),
        "trace_events": trace_events,
        "created_at": case.get("created_at"),
        "updated_at": case.get("updated_at"),
    }
