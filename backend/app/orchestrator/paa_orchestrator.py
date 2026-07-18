"""PAA Orchestrator — điều phối pipeline TUẦN TỰ (Nguyên tắc V):

    Research (7 tool SONG SONG) → Valuation → Risk → Advisory

Mỗi bước hoàn tất: (1) lưu field tương ứng vào CaseSession, (2) ghi 1 TraceEvent,
(3) publish 1 SSE event (chat_message + active_tab). Không bước nào tự set duyệt/
từ chối tín dụng — chỉ set ``status=completed`` khi toàn pipeline xong.

Điều phối bằng code async thường (fallback chắc chắn chạy) thay vì ADK
SequentialAgent — vì các agent đã là hàm tất định, không cần LLM để chạy; giữ
đúng thứ tự phụ thuộc dữ liệu.
"""

from __future__ import annotations

import time

from app.agents import advisory_agent, research_agent, risk_agent, valuation_agent
from app.orchestrator import event_bus

# Suy ra tab InfoPanel active từ component (frontend FR-011).
# 1=Nhập thông tin, 2=Kết quả tra cứu, 3=Định giá, 4=Rủi ro, 5=Checklist/Biên bản.
_COMPONENT_TAB = {
    "intake": 1,
    "research_agent": 2,
    "valuation_agent": 3,
    "risk_agent": 4,
    "advisory_agent": 5,
}


def tab_for_component(component: str | None) -> int:
    return _COMPONENT_TAB.get(component or "", 1)


def _fmt_ty(value) -> str:
    try:
        return f"{float(value) / 1_000_000_000:.2f} tỷ"
    except (TypeError, ValueError):
        return "N/A"


class _CancelledError(Exception):
    pass


async def run_appraisal_pipeline(case_id: str, store) -> None:
    """Chạy toàn pipeline cho 1 case. Bọc lỗi để không sập process/loop."""
    t0 = time.monotonic()

    def log(step_name, component, chat_message, input_summary="", output_summary=""):
        t_offset = time.monotonic() - t0
        store.add_trace_event(
            case_id, step_name, component, t_offset,
            input_summary=input_summary,
            output_summary=output_summary or chat_message,
        )
        event_bus.publish(case_id, {
            "step_name": step_name,
            "component": component,
            "active_tab": tab_for_component(component),
            "chat_message": chat_message,
            "t_offset_seconds": round(t_offset, 3),
            "status": "processing",
        })

    def ensure_active():
        case = store.get_case(case_id)
        if case and case.get("status") == "cancelled":
            raise _CancelledError()

    try:
        case = store.get_case(case_id)
        if case is None:
            return
        subject_property = case.get("subject_property_json") or {}

        log("Hệ thống tiếp nhận yêu cầu thẩm định", "intake",
            "Đã tiếp nhận yêu cầu. Bắt đầu tra cứu 7 nguồn dữ liệu song song…",
            input_summary=str(subject_property.get("address")))

        # --- 1. Research (song song) ---
        ensure_active()
        lookup_result = await research_agent.run(subject_property)
        store.update_fields(case_id, lookup_result_json=lookup_result)
        issues = [
            k for k, v in lookup_result.items()
            if isinstance(v, dict) and v.get("status") in ("partial", "error")
        ]
        note = (f" Phát hiện {len(issues)} nguồn cần lưu ý." if issues else "")
        log("Đã có kết quả tra cứu", "research_agent",
            "Đã có kết quả tra cứu — xem tab Kết quả tra cứu." + note,
            output_summary=f"7 nguồn tra cứu hoàn tất; {len(issues)} nguồn partial/error.")

        # --- 2. Valuation ---
        ensure_active()
        valuation_result = await valuation_agent.run(subject_property, lookup_result)
        store.update_fields(case_id, valuation_result_json=valuation_result)
        est = valuation_result.get("estimated_value")
        conf = valuation_result.get("confidence_score")
        log("Bộ máy định giá hoàn tất", "valuation_agent",
            f"Định giá đề xuất: {_fmt_ty(est)} (độ tin cậy {conf}). Xem tab Định giá.",
            output_summary=f"estimated_value={est}, confidence={conf}, "
                           f"comparables={valuation_result.get('comparables_used')}")

        # --- 3. Risk ---
        ensure_active()
        risk_result = await risk_agent.run(valuation_result, lookup_result)
        store.update_fields(case_id, risk_result_json=risk_result)
        score = risk_result.get("asset_risk_score")
        tier = risk_result.get("risk_tier")
        ltv = risk_result.get("recommended_ltv_cap")
        log("Bộ máy chấm điểm rủi ro hoàn tất", "risk_agent",
            f"Điểm rủi ro tài sản: {score}/100 ({tier}), LTV đề xuất {ltv}. Xem tab Rủi ro.",
            output_summary=f"asset_risk_score={score}, tier={tier}, ltv_cap={ltv}")

        # --- 4. Advisory (checklist + nháp biên bản) ---
        ensure_active()
        advisory = await advisory_agent.run(subject_property, valuation_result, risk_result)
        store.update_fields(
            case_id,
            checklist_json=advisory.get("checklist"),
            report_draft_json=advisory.get("draft_report"),
        )
        n_items = len(advisory.get("checklist") or [])
        log("Copilot sinh nháp biên bản & checklist", "advisory_agent",
            f"Đã sinh nháp biên bản và {n_items} mục checklist cần xác minh. "
            "Bản nháp CHỜ thẩm định viên xác nhận.",
            output_summary=f"checklist_items={n_items}")

        # --- Hoàn tất ---
        store.set_status(case_id, "completed")
        event_bus.publish(case_id, {
            "step_name": "Hoàn tất pipeline",
            "component": "orchestrator",
            "active_tab": 5,
            "chat_message": "Hoàn tất phân tích. Kết quả là ĐỀ XUẤT, cần con người xác minh trước khi quyết định.",
            "t_offset_seconds": round(time.monotonic() - t0, 3),
            "status": "completed",
        })

    except _CancelledError:
        event_bus.publish(case_id, {
            "step_name": "Đã huỷ hồ sơ", "component": "orchestrator",
            "active_tab": tab_for_component(None),
            "chat_message": "Hồ sơ đã bị huỷ.",
            "t_offset_seconds": round(time.monotonic() - t0, 3),
            "status": "cancelled",
        })
    except Exception as exc:  # noqa: BLE001 - không để lỗi làm chết loop/process
        store.add_trace_event(
            case_id, "Lỗi pipeline", "orchestrator", time.monotonic() - t0,
            output_summary=f"{type(exc).__name__}: {exc}",
        )
        event_bus.publish(case_id, {
            "step_name": "Lỗi pipeline", "component": "orchestrator",
            "active_tab": tab_for_component(None),
            "chat_message": f"Pipeline gặp lỗi: {exc}",
            "t_offset_seconds": round(time.monotonic() - t0, 3),
            "status": "error",
        })
