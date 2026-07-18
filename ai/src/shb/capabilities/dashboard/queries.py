"""Read tools backing Màn 5 — Dashboard: sidebar case history, the 4 KPI
tiles, the "Tổng hợp theo từng bước" summaries, and the agent trace timeline.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shb.db.models_paa import (
    AgentTraceEvent,
    AppraisalCase,
    DashboardStepSummary,
    PropertyPhysicalInfo,
    RiskAssessmentResult,
    ValuationResult,
)


async def list_case_history(session: AsyncSession, limit: int = 50) -> list[dict]:
    """Equivalent of ``v_case_history`` — sidebar "Lịch sử hồ sơ" list, most-recent first."""
    stmt = (
        select(AppraisalCase, PropertyPhysicalInfo.address)
        .outerjoin(PropertyPhysicalInfo, PropertyPhysicalInfo.case_id == AppraisalCase.case_id)
        .order_by(AppraisalCase.updated_at.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "case_id": case.case_id,
            "address": address,
            "status": case.status.value,
            "updated_at": case.updated_at.isoformat(),
        }
        for case, address in rows
    ]


async def get_dashboard_kpi(case_id: str, session: AsyncSession) -> dict | None:
    """Equivalent of ``v_dashboard_kpi`` — the 4 KPI tiles at the top of the Dashboard.

    Returns ``None`` if either the valuation or the risk step hasn't been
    computed yet for this case (inner join semantics, matching the view).
    """
    stmt = (
        select(ValuationResult, RiskAssessmentResult)
        .join(RiskAssessmentResult, RiskAssessmentResult.case_id == ValuationResult.case_id)
        .where(ValuationResult.case_id == case_id)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    valuation, risk = row
    return {
        "case_id": case_id,
        "proposed_value_vnd": valuation.proposed_value_vnd,
        "value_range_low_vnd": valuation.value_range_low_vnd,
        "value_range_high_vnd": valuation.value_range_high_vnd,
        "valuation_confidence_pct": valuation.confidence_pct,
        "risk_score": risk.risk_score,
        "risk_label": risk.risk_label.value,
        "ltv_proposed_pct": risk.ltv_proposed_pct,
    }


async def get_step_summaries(case_id: str, session: AsyncSession) -> list[DashboardStepSummary]:
    """Fetch the 4 "Tổng hợp theo từng bước" rows, in step order."""
    stmt = (
        select(DashboardStepSummary)
        .where(DashboardStepSummary.case_id == case_id)
        .order_by(DashboardStepSummary.step_number)
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_trace_events(case_id: str, session: AsyncSession) -> list[AgentTraceEvent]:
    """Fetch the agent execution trace timeline, in chronological order."""
    stmt = (
        select(AgentTraceEvent)
        .where(AgentTraceEvent.case_id == case_id)
        .order_by(AgentTraceEvent.event_order, AgentTraceEvent.seconds_offset)
    )
    return list((await session.execute(stmt)).scalars().all())
