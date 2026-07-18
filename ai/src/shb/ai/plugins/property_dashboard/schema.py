"""Pydantic schemas for the property_dashboard plugin (Màn 5 — Dashboard).

Aggregates Màn 1–4 into the sign-off dashboard: KPI tiles, deterministic lending
verdict + max loan, the 4 step summaries (LLM-worded, fail-safe template), the
agent trace timeline and the case-history sidebar. Numbers/decision are 100%
deterministic; the LLM only rewords the summaries. Enum values match ``models_paa``.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class VerdictDecision(StrEnum):
    """Kết luận cho vay (3 bậc)."""

    DE_XUAT_CHO_VAY = "de_xuat_cho_vay"
    CAN_NHAC = "can_nhac"
    TU_CHOI = "tu_choi"


class SeverityLevel(StrEnum):
    """Mức nghiêm trọng (khớp enum DB ``severity_level``)."""

    THAP = "thap"
    TRUNG_BINH = "trung_binh"
    CAO = "cao"
    NGHIEM_TRONG = "nghiem_trong"


class DashboardKpi(BaseModel):
    """4 ô KPI đầu Dashboard (↔ v_dashboard_kpi: valuation_result + risk_assessment_result)."""

    proposed_value_vnd: int
    value_range_low_vnd: int | None = None
    value_range_high_vnd: int | None = None
    valuation_confidence_pct: int | None = None
    risk_score: int
    risk_label: SeverityLevel
    ltv_proposed_pct: int


class VerdictOut(BaseModel):
    """Kết luận cho vay xác định (engine synthesis) — khối "kết luận" Dashboard."""

    decision: VerdictDecision
    headline: str
    max_loan_vnd: int | None = None
    downgraded: bool = False
    reasons: list[str] = Field(default_factory=list)


class StepSummaryOut(BaseModel):
    """1 dòng "Tổng hợp theo từng bước" (↔ dashboard_step_summary)."""

    step_number: int
    title: str
    summary_text: str
    generated_by: str = "template"  # "llm" | "template"


class TraceEventOut(BaseModel):
    """1 mốc timeline "Trace thực thi PAA" (↔ agent_trace_event)."""

    seconds_offset: float
    actor: str
    title: str
    description: str | None = None


class CaseHistoryOut(BaseModel):
    """1 mục sidebar "Lịch sử hồ sơ" (↔ v_case_history)."""

    case_id: str
    address: str | None = None
    status: str
    updated_at: str


class PropertyDashboardInput(BaseModel):
    """Input: mã hồ sơ cần tổng hợp Dashboard."""

    case_id: str = Field(..., description="Mã hồ sơ (REQ-...).")


class PropertyDashboardOutput(BaseModel):
    """Output Màn 5: KPI + verdict + tóm tắt 4 bước + kết luận + trace + lịch sử."""

    case_id: str
    kpi: DashboardKpi | None = None
    verdict: VerdictOut | None = None
    step_summaries: list[StepSummaryOut] = Field(default_factory=list)
    overall_narrative: str | None = None
    trace: list[TraceEventOut] = Field(default_factory=list)
    case_history: list[CaseHistoryOut] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
