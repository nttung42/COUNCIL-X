"""Valuation Agent — gọi ``calculate_valuation`` (tuần tự sau Research).

Bóc comparables + amenities từ lookup_result rồi truyền vào engine định giá đã có
sẵn (Wave 1). Không tự viết lại logic định giá.
"""

from __future__ import annotations

import asyncio

from app.tools.calculate_valuation import calculate_valuation


def _envelope_data(lookup_result: dict, key: str) -> dict:
    env = (lookup_result or {}).get(key) or {}
    data = env.get("data") if isinstance(env, dict) else None
    return data if isinstance(data, dict) else {}


class ValuationAgent:
    async def run(self, subject_property: dict, lookup_result: dict) -> dict:
        comparables = _envelope_data(lookup_result, "market_price").get("comparables") or []
        amenities = _envelope_data(lookup_result, "neighborhood_amenity").get("amenities") or []
        return await asyncio.to_thread(
            calculate_valuation,
            subject_property,
            comparables=comparables,
            amenities=amenities,
        )


valuation_agent = ValuationAgent()
