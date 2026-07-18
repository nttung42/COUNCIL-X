"""Read tools backing Màn 3 — Định giá: the aggregate result, the 3 weighted
methods, and the 5 confidence factors. These are the "tools" a
``valuation`` graph node (or a report/chat node answering "vì sao giá này?")
calls — no business logic here, just typed SQL access.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shb.db.models_paa import (
    ValuationConfidenceFactor,
    ValuationMethod,
    ValuationPriceIndexPoint,
    ValuationResult,
)


async def get_valuation_result(case_id: str, session: AsyncSession) -> ValuationResult | None:
    """Fetch the aggregate valuation row (proposed_value/range/confidence) for a case."""
    return await session.get(ValuationResult, case_id)


async def get_valuation_methods(case_id: str, session: AsyncSession) -> list[ValuationMethod]:
    """Fetch the 3 valuation methods (sales_comparison/hedonic_ml/cost_approach)."""
    stmt = select(ValuationMethod).where(ValuationMethod.case_id == case_id)
    return list((await session.execute(stmt)).scalars().all())


async def get_confidence_factors(
    case_id: str, session: AsyncSession
) -> list[ValuationConfidenceFactor]:
    """Fetch the 5 factors composing the "Cấu thành độ tin cậy tổng" score."""
    stmt = select(ValuationConfidenceFactor).where(ValuationConfidenceFactor.case_id == case_id)
    return list((await session.execute(stmt)).scalars().all())


async def get_price_index_series(
    case_id: str, session: AsyncSession
) -> list[ValuationPriceIndexPoint]:
    """Fetch the price-index sparkline series for a case, in display order."""
    stmt = (
        select(ValuationPriceIndexPoint)
        .where(ValuationPriceIndexPoint.case_id == case_id)
        .order_by(ValuationPriceIndexPoint.display_order)
    )
    return list((await session.execute(stmt)).scalars().all())
