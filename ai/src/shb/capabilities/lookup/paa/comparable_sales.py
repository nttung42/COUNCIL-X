"""``comparable_sales`` adapter — giao dịch so sánh khu vực, giá/m² (nền cho
Valuation Engine's ``sales_comparison`` method). The one adapter that reads a
second table (``market_comparable``) on top of the shared ``lookup_finding``
row, so it overrides :meth:`lookup` instead of relying on the base default.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shb.capabilities.lookup.base import AdapterResult, LookupAdapter, _num
from shb.db.models_paa import LookupCategory, MarketComparable


class ComparableSalesAdapter(LookupAdapter):
    """Trả về danh sách giao dịch so sánh trong bán kính + nhận định PAA."""

    key = "comparable_sales"
    label = "Giao dịch so sánh khu vực"
    category = LookupCategory.MARKET_PRICE

    async def lookup(self, case_id: str, session: AsyncSession) -> AdapterResult:
        finding = await self._load_finding(case_id, session)
        result = self._to_result(finding)

        stmt = (
            select(MarketComparable)
            .where(MarketComparable.case_id == case_id)
            .order_by(MarketComparable.display_order)
        )
        comps = (await session.execute(stmt)).scalars().all()
        result.data["comparables"] = [
            {
                "address": c.comp_address,
                "distance_km": _num(c.distance_km),
                "area_sqm": _num(c.area_sqm),
                "transaction_date": (
                    c.transaction_date.isoformat() if c.transaction_date else None
                ),
                "price_per_sqm_vnd": c.price_per_sqm_vnd,
            }
            for c in comps
        ]
        return result
