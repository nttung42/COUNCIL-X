"""property_dashboard AI service (async, SSE) — Màn 5 Dashboard.

Aggregates a case's Màn 1–4 into the sign-off dashboard: KPI tiles, a
deterministic lending verdict + max loan (:mod:`shb.capabilities.dashboard.synthesis`),
the 4 step summaries (LLM-worded via :mod:`~shb.capabilities.dashboard.narrator`,
fail-safe to templates), the agent trace timeline and the case-history sidebar.
Numbers and the decision are 100% deterministic — the LLM only rewords prose.
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from shb.ai.plugins.base import AIServiceContext, AIServiceMeta, BaseAIService
from shb.ai.plugins.property_dashboard.schema import (
    CaseHistoryOut,
    DashboardKpi,
    PropertyDashboardInput,
    PropertyDashboardOutput,
    StepSummaryOut,
    TraceEventOut,
    VerdictOut,
)
from shb.capabilities.dashboard.narrator import (
    DashboardFacts,
    StepFact,
    narrate_dashboard,
)
from shb.capabilities.dashboard.queries import get_trace_events, list_case_history
from shb.capabilities.dashboard.synthesis import (
    SynthesisInputs,
    VerdictFlag,
    compute_verdict,
)
from shb.db.models_paa import (
    LookupFinding,
    PropertyLegalInfo,
    PropertyPhysicalInfo,
    RiskAssessmentResult,
    RiskFlag,
    RiskGroup,
    ValuationResult,
    VerificationStatus,
)

logger = logging.getLogger(__name__)


def _report(ctx, value: int) -> None:
    cb = getattr(ctx, "update_progress", None)
    if callable(cb):
        try:
            cb(value)
        except Exception:  # pragma: no cover - progress is best-effort
            logger.debug("progress callback failed", exc_info=True)


def _vnd(value: int | None) -> str:
    return f"{value:,} đ" if value is not None else "chưa có"


def _step1_text(phys, legal) -> str:
    parts = []
    if phys is not None:
        parts.append(
            f"Tài sản: {phys.property_type or 'BĐS'} tại {phys.address or 'địa chỉ chưa rõ'}"
            + (f", diện tích đất {phys.land_area_sqm} m²" if phys.land_area_sqm else "")
            + "."
        )
    if legal is not None:
        parts.append(
            f"Giấy tờ: {legal.certificate_type or 'chưa rõ'}"
            + (f", {legal.ownership_form}" if getattr(legal, "ownership_form", None) else "")
            + (
                f". Tình trạng thế chấp: {legal.current_mortgage_status}."
                if getattr(legal, "current_mortgage_status", None)
                else "."
            )
        )
    return " ".join(parts) or "Chưa có dữ liệu hồ sơ/tài sản (Màn 1)."


def _step2_text(findings: list) -> str:
    if not findings:
        return "Chưa có dữ liệu tra cứu (Màn 2)."
    badges = {}
    for f in findings:
        badges[f.status_badge.value] = badges.get(f.status_badge.value, 0) + 1
    breakdown = ", ".join(f"{n} {b}" for b, n in badges.items())
    return f"Đã tra cứu {len(findings)} hạng mục (pháp lý, thanh khoản, môi trường, danh tiếng): {breakdown}."


def _step3_text(val) -> str:
    if val is None:
        return "Chưa có kết quả định giá (Màn 3)."
    rng = ""
    if val.value_range_low_vnd and val.value_range_high_vnd:
        rng = f" (khoảng {_vnd(val.value_range_low_vnd)}–{_vnd(val.value_range_high_vnd)})"
    conf = f", độ tin cậy {val.confidence_pct}%" if val.confidence_pct is not None else ""
    return f"Giá trị đề xuất {_vnd(val.proposed_value_vnd)}{rng}{conf}."


def _step4_text(risk, n_flags: int) -> str:
    if risk is None:
        return "Chưa có kết quả chấm rủi ro (Màn 4)."
    flags_note = f" Có {n_flags} cảnh báo cần lưu ý." if n_flags else ""
    return (
        f"Điểm rủi ro {risk.risk_score}/100 ({risk.risk_label.value}), "
        f"LTV đề xuất tối đa {risk.ltv_proposed_pct}%.{flags_note}"
    )


class PropertyDashboardService(BaseAIService):
    """Aggregate Màn 1–4 into the sign-off Dashboard (Màn 5)."""

    meta = AIServiceMeta(
        id="property_dashboard",
        name="Dashboard tổng hợp",
        description=(
            "Tổng hợp Màn 1–4 thành dashboard ký duyệt: KPI, kết luận cho vay + hạn mức "
            "(xác định 100%), tóm tắt 4 bước (LLM diễn giải, fail-safe template), trace và "
            "lịch sử hồ sơ."
        ),
        version="0.1.0",
        is_async=True,
        accepts_file=False,
    )

    InputSchema = PropertyDashboardInput
    OutputSchema = PropertyDashboardOutput

    async def run(
        self, input_data: PropertyDashboardInput, ctx: AIServiceContext
    ) -> PropertyDashboardOutput:
        """Read Màn 1–4, compute the verdict, narrate the summaries, assemble Màn 5."""
        factory = ctx.db_session_factory
        if factory is None:
            raise RuntimeError("property_dashboard requires ctx.db_session_factory.")
        case_id = input_data.case_id

        async with factory() as session:
            phys = await session.get(PropertyPhysicalInfo, case_id)
            legal = await session.get(PropertyLegalInfo, case_id)
            val = await session.get(ValuationResult, case_id)
            risk = await session.get(RiskAssessmentResult, case_id)
            findings = list(
                (
                    await session.execute(
                        select(LookupFinding).where(LookupFinding.case_id == case_id)
                    )
                ).scalars()
            )
            flags = list(
                (
                    await session.execute(
                        select(RiskFlag)
                        .where(RiskFlag.case_id == case_id)
                        .order_by(RiskFlag.display_order)
                    )
                ).scalars()
            )
            group_key_by_id = {
                g.id: g.group_key.value
                for g in (
                    await session.execute(select(RiskGroup).where(RiskGroup.case_id == case_id))
                ).scalars()
            }
            trace_rows = await get_trace_events(case_id, session)
            history = await list_case_history(session)
        _report(ctx, 50)

        warnings: list[str] = []
        trace = [
            TraceEventOut(
                seconds_offset=float(t.seconds_offset),
                actor=t.actor,
                title=t.title,
                description=t.description,
            )
            for t in trace_rows
        ]
        case_history = [CaseHistoryOut(**h) for h in history]

        # --- KPI + verdict (deterministic) -----------------------------------
        kpi = None
        verdict_out = None
        overall_template = "Chưa đủ dữ liệu định giá và rủi ro để đưa ra kết luận."
        if val is not None and risk is not None:
            kpi = DashboardKpi(
                proposed_value_vnd=val.proposed_value_vnd,
                value_range_low_vnd=val.value_range_low_vnd,
                value_range_high_vnd=val.value_range_high_vnd,
                valuation_confidence_pct=val.confidence_pct,
                risk_score=risk.risk_score,
                risk_label=risk.risk_label.value,
                ltv_proposed_pct=risk.ltv_proposed_pct,
            )
        if risk is not None:
            verdict_flags = [
                VerdictFlag(
                    group_key=group_key_by_id.get(f.linked_risk_group, _infer_group(f.title)),
                    severity=f.severity.value,
                    verified=f.verified_status == VerificationStatus.DA_XAC_THUC,
                    title=f.title,
                )
                for f in flags
            ]
            verdict = compute_verdict(
                SynthesisInputs(
                    risk_label=risk.risk_label.value,
                    proposed_value_vnd=getattr(val, "proposed_value_vnd", None),
                    ltv_proposed_pct=risk.ltv_proposed_pct,
                    flags=verdict_flags,
                )
            )
            verdict_out = VerdictOut(
                decision=verdict.decision,
                headline=verdict.headline,
                max_loan_vnd=verdict.max_loan_vnd,
                downgraded=verdict.downgraded,
                reasons=verdict.reasons,
            )
            overall_template = (
                f"Kết luận: {verdict.headline}. "
                f"Hạn mức cho vay tối đa {_vnd(verdict.max_loan_vnd)}. "
                f"Điểm rủi ro {risk.risk_score}/100 ({risk.risk_label.value})."
            )
        else:
            warnings.append(
                f"Chưa có kết quả rủi ro (Màn 4) cho hồ sơ '{case_id}' — chưa thể kết luận cho vay."
            )
        if val is None:
            warnings.append(f"Chưa có kết quả định giá (Màn 3) cho hồ sơ '{case_id}'.")

        # --- step summaries (LLM-worded, fail-safe template) -----------------
        facts = DashboardFacts(
            steps=[
                StepFact(1, "Hồ sơ & tài sản", _step1_text(phys, legal)),
                StepFact(2, "Tra cứu", _step2_text(findings)),
                StepFact(3, "Định giá", _step3_text(val)),
                StepFact(4, "Rủi ro", _step4_text(risk, len(flags))),
            ],
            overall_template=overall_template,
        )
        narration = await narrate_dashboard(facts)
        title_by_step = {s.step_number: s.title for s in facts.steps}
        step_summaries = [
            StepSummaryOut(
                step_number=n,
                title=title_by_step[n],
                summary_text=text,
                generated_by=narration.generated_by,
            )
            for n, text in narration.step_summaries
        ]

        _report(ctx, 100)
        return PropertyDashboardOutput(
            case_id=case_id,
            kpi=kpi,
            verdict=verdict_out,
            step_summaries=step_summaries,
            overall_narrative=narration.overall_narrative,
            trace=trace,
            case_history=case_history,
            warnings=warnings,
        )


def _infer_group(title: str | None) -> str:
    """Fallback group_key from a flag title when linked_risk_group is missing."""
    t = (title or "").lower()
    if "pháp lý" in t:
        return "legal"
    if "thanh khoản" in t:
        return "liquidity"
    if "biến động" in t or "giá" in t:
        return "price_volatility"
    if "vật lý" in t or "môi trường" in t:
        return "physical_environment"
    if "danh tiếng" in t or "tâm linh" in t:
        return "reputation"
    return "legal" if "thế chấp" in t or "tranh chấp" in t else "reputation"
