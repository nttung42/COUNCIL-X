"""Prepare the DEMO case (REQ-2026-2000) so every Màn is live-complete.

The seed gives REQ-2026-2000 full Màn 1+2+3 data but no Màn-4 result and no
agent trace — so the live Dashboard (F5) shows "chưa thể kết luận". This script
completes the case USING THE REAL ENGINE (no hand-typed numbers):

  1. Runs property_risk (F4) on the seeded data → persists
     risk_assessment_result + risk_group + risk_flag (like the backend would).
  2. Inserts a realistic agent_trace_event timeline (labels only — the numbers
     all come from the engines).
  3. Re-runs property_dashboard (F5) and prints the verdict as verification.

Idempotent: safe to re-run (clears the case's Màn-4 + trace rows first).
Run from ai/ (DATABASE_URL from .env):  .venv/Scripts/python.exe scripts/prepare_demo_case.py
"""

from __future__ import annotations

import asyncio

from sqlalchemy import delete

from shb.ai.plugins.base import AIServiceContext
from shb.ai.plugins.property_dashboard.schema import PropertyDashboardInput
from shb.ai.plugins.property_dashboard.service import PropertyDashboardService
from shb.ai.plugins.property_risk.schema import PropertyRiskInput
from shb.ai.plugins.property_risk.service import PropertyRiskService
from shb.core.db import AsyncSessionLocal
from shb.db.models_paa import (
    AgentTraceEvent,
    RiskAssessmentResult,
    RiskFlag,
    RiskGroup,
    SeverityLevel,
    VerificationStatus,
)

CASE_ID = "REQ-2026-2000"

TRACE = [
    (0.4, "Orchestrator", "Khởi tạo phiên thẩm định", "Nhận hồ sơ, mở pipeline 5 bước."),
    (
        2.1,
        "Intake Agent",
        "Trích xuất 4 tài liệu",
        "Phân loại + trích 24 trường, gắn nguồn gốc và vùng trích xuất.",
    ),
    (
        9.8,
        "Research Agent",
        "Tra cứu 7 nguồn",
        "Giá thị trường, quy hoạch, pháp lý, tiện ích, môi trường, thanh khoản, dư luận.",
    ),
    (
        14.6,
        "Valuation Engine",
        "Định giá 3 phương pháp",
        "So sánh giao dịch + hedonic + chi phí; hợp nhất theo trọng số.",
    ),
    (
        17.2,
        "Risk Engine",
        "Chấm điểm rủi ro 5 nhóm",
        "Điểm rủi ro → khung LTV chính sách; sinh cảnh báo.",
    ),
    (
        19.0,
        "Dashboard Agent",
        "Tổng hợp & kết luận",
        "KPI, hạn mức cho vay tối đa, tóm tắt từng bước.",
    ),
]


async def main() -> None:
    """Compute + persist Màn 4 for the demo case, then verify via F5."""
    ctx = AIServiceContext(
        user_id="demo-prep", service_id="property_risk", db_session_factory=AsyncSessionLocal
    )

    print(f"1/3  Tính F4 (engine thật) cho {CASE_ID} ...")
    out4 = await PropertyRiskService().run(PropertyRiskInput(case_id=CASE_ID), ctx)
    a = out4.assessment
    if a is None:
        raise SystemExit("F4 không trả assessment — thiếu dữ liệu Màn 1?")
    print(f"     risk_score={a.risk_score} label={a.risk_label.value} LTV={a.ltv_proposed_pct}%")

    print("2/3  Persist Màn 4 + trace ...")
    async with AsyncSessionLocal() as s:
        for model in (RiskFlag, RiskGroup, RiskAssessmentResult, AgentTraceEvent):
            await s.execute(delete(model).where(model.case_id == CASE_ID))
        s.add(
            RiskAssessmentResult(
                case_id=CASE_ID,
                risk_score=a.risk_score,
                risk_label=SeverityLevel(a.risk_label.value),
                ltv_proposed_pct=a.ltv_proposed_pct,
                risk_inference_text=a.risk_inference_text,
            )
        )
        group_ids: dict[str, str] = {}
        for g in out4.groups:
            rg = RiskGroup(
                case_id=CASE_ID,
                group_key=g.group_key.value,
                label=g.label,
                weight_pct=g.weight_pct,
                score=g.score,
                raw_findings=g.signals,
                source_label=g.group_key.value,
            )
            s.add(rg)
            await s.flush()
            group_ids[g.label] = rg.id
        for i, fl in enumerate(out4.flags):
            s.add(
                RiskFlag(
                    case_id=CASE_ID,
                    severity=SeverityLevel(fl.severity.value),
                    title=fl.title,
                    description=fl.description,
                    confidence_pct=fl.confidence_pct,
                    verified_status=(
                        VerificationStatus.DA_XAC_THUC
                        if fl.verified
                        else VerificationStatus.CHUA_XAC_THUC
                    ),
                    linked_risk_group=group_ids.get(fl.title),
                    display_order=i,
                )
            )
        for order, (sec, actor, title, desc) in enumerate(TRACE):
            s.add(
                AgentTraceEvent(
                    case_id=CASE_ID,
                    seconds_offset=sec,
                    actor=actor,
                    title=title,
                    description=desc,
                    event_order=order,
                )
            )
        await s.commit()
    print(
        f"     đã ghi 1 assessment + {len(out4.groups)} nhóm + {len(out4.flags)} flag + {len(TRACE)} trace"
    )

    print("3/3  Verify qua F5 (dashboard) ...")
    out5 = await PropertyDashboardService().run(PropertyDashboardInput(case_id=CASE_ID), ctx)
    v = out5.verdict
    k = out5.kpi
    assert v is not None and k is not None, "F5 vẫn thiếu verdict/KPI!"
    print(
        f"     KPI: value={k.proposed_value_vnd:,} risk={k.risk_score}/{k.risk_label} LTV={k.ltv_proposed_pct}%"
    )
    print(f"     VERDICT: {v.decision} — {v.headline} | hạn mức {v.max_loan_vnd:,} đ")
    print(f"     trace={len(out5.trace)} | warnings={out5.warnings}")
    print("DONE — case demo sẵn sàng cho Màn 5 live.")


if __name__ == "__main__":
    asyncio.run(main())
