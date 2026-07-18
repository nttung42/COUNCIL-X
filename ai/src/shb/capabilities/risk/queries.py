"""Read tools backing Màn 4 — Rủi ro: the aggregate score/LTV, the 5 weighted
risk groups, the flag list, and the (static, admin-editable) LTV policy table.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shb.db.models_paa import RiskAssessmentResult, RiskFlag, RiskGroup, RiskLtvPolicyBand


async def get_risk_assessment(case_id: str, session: AsyncSession) -> RiskAssessmentResult | None:
    """Fetch the aggregate risk row (risk_score/risk_label/ltv_proposed_pct)."""
    return await session.get(RiskAssessmentResult, case_id)


async def get_risk_groups(case_id: str, session: AsyncSession) -> list[RiskGroup]:
    """Fetch the 5 weighted risk groups (pháp lý/thanh khoản/biến động giá/vật lý-môi trường/danh tiếng)."""
    stmt = select(RiskGroup).where(RiskGroup.case_id == case_id)
    return list((await session.execute(stmt)).scalars().all())


async def get_risk_flags(case_id: str, session: AsyncSession) -> list[RiskFlag]:
    """Fetch "Flags cần lưu ý" for a case, in display order."""
    stmt = select(RiskFlag).where(RiskFlag.case_id == case_id).order_by(RiskFlag.display_order)
    return list((await session.execute(stmt)).scalars().all())


async def get_ltv_for_score(risk_score: int, session: AsyncSession) -> RiskLtvPolicyBand | None:
    """Resolve the LTV policy band applicable to a given asset risk score (0-100).

    Equivalent to ``WHERE min_score <= :score AND (max_score IS NULL OR :score <= max_score)``;
    done in Python after a small ``min_score``-filtered fetch since ``max_score``
    can be NULL (the ">60" open-ended band) and cross-dialect NULL-safe
    comparisons are simplest expressed this way.
    """
    stmt = select(RiskLtvPolicyBand).where(RiskLtvPolicyBand.min_score <= risk_score)
    for band in (await session.execute(stmt)).scalars().all():
        if band.max_score is None or risk_score <= band.max_score:
            return band
    return None


async def list_ltv_policy_bands(session: AsyncSession) -> list[RiskLtvPolicyBand]:
    """Fetch all 4 configured LTV policy bands, ordered by ``id``."""
    stmt = select(RiskLtvPolicyBand).order_by(RiskLtvPolicyBand.id)
    return list((await session.execute(stmt)).scalars().all())
