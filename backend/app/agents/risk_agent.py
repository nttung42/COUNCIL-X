"""Risk Agent — gọi ``calculate_asset_risk_score`` (tuần tự sau Valuation).

Truyền thẳng ENVELOPE của các lookup tool (engine tự đọc qua ``_data()``), cùng
comparables để tính biến động giá. Không viết lại logic chấm điểm.
"""

from __future__ import annotations

import asyncio

from app.tools.calculate_asset_risk_score import calculate_asset_risk_score


class RiskAgent:
    async def run(self, valuation_result: dict, lookup_result: dict) -> dict:
        lr = lookup_result or {}
        comparables = (
            ((lr.get("market_price") or {}).get("data") or {}).get("comparables") or []
        )
        return await asyncio.to_thread(
            calculate_asset_risk_score,
            valuation=valuation_result,
            legal_envelope=lr.get("legal_status"),
            planning_envelope=lr.get("planning_zoning"),
            liquidity_envelope=lr.get("liquidity_stat"),
            environmental_envelope=lr.get("environmental_risk"),
            stigma_envelope=lr.get("stigma_reputation"),
            comparables=comparables,
        )


risk_agent = RiskAgent()
