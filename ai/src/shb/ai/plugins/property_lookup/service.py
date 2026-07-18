"""property_lookup AI service (sync, DB-reading) — Màn 2 Kết quả tra cứu.

Reads the 7 pre-populated lookup findings + comparable transactions for a case
(seeded demo data, or written by a research pipeline later) via the shared
:mod:`shb.capabilities.lookup` adapters, and assembles the Màn 2 output.

It only reads the DB, so it is **synchronous** (``is_async=False``) — no Celery
job needed. The DB session is opened from ``ctx.db_session_factory`` injected by
the API/worker, so the plugin never touches the engine directly.
"""

from __future__ import annotations

import logging

from shb.ai.plugins.base import AIServiceContext, AIServiceMeta, BaseAIService
from shb.ai.plugins.property_lookup.schema import (
    LookupFindingOut,
    MarketComparableOut,
    PropertyLookupInput,
    PropertyLookupOutput,
)
from shb.capabilities.lookup.base import AdapterResult
from shb.capabilities.lookup.registry import get_lookup_registry

logger = logging.getLogger(__name__)


def _to_finding(result: AdapterResult) -> LookupFindingOut:
    """Map a lookup :class:`AdapterResult` into the Màn 2 finding shape."""
    return LookupFindingOut(
        category=result.category,
        tool_name=result.data.get("tool_name") or result.adapter_key,
        title=result.data.get("title") or result.label or result.adapter_key,
        status_badge=result.status_badge or "chua_xac_thuc",
        raw_findings=list(result.data.get("raw_findings") or []),
        inference_text=result.data.get("inference"),
        source_label=result.source,
        confidence_pct=round(result.confidence * 100),
    )


def _to_comparables(results: list[AdapterResult]) -> list[MarketComparableOut]:
    """Pull the comparable-sales table out of the market_price adapter result."""
    comparables: list[MarketComparableOut] = []
    for result in results:
        for comp in result.data.get("comparables") or []:
            comparables.append(
                MarketComparableOut(
                    address=comp.get("address", ""),
                    distance_km=comp.get("distance_km"),
                    area_sqm=comp.get("area_sqm"),
                    transaction_date=comp.get("transaction_date"),
                    price_per_sqm_vnd=comp.get("price_per_sqm_vnd") or 0,
                )
            )
    return comparables


class PropertyLookupService(BaseAIService):
    """Serve a case's 7 lookup findings + comparable transactions (Màn 2)."""

    meta = AIServiceMeta(
        id="property_lookup",
        name="Kết quả tra cứu bất động sản",
        description=(
            "Đọc kết quả 7 nguồn tra cứu (giá thị trường, quy hoạch, pháp lý, tiện ích, "
            "môi trường, thanh khoản, dư luận) và bảng giao dịch so sánh của một hồ sơ."
        ),
        version="0.1.0",
        # Runs as an async job so it shares the unified SSE progress channel
        # (POST run -> job_id -> GET /jobs/{id}/stream) with the heavy services.
        # The read itself is fast; the job completes almost immediately.
        is_async=True,
        accepts_file=False,
    )

    InputSchema = PropertyLookupInput
    OutputSchema = PropertyLookupOutput

    async def run(
        self, input_data: PropertyLookupInput, ctx: AIServiceContext
    ) -> PropertyLookupOutput:
        """Read the case's lookup findings + comparables and assemble the output."""
        factory = ctx.db_session_factory
        if factory is None:
            raise RuntimeError(
                "property_lookup requires ctx.db_session_factory to read the database."
            )

        async with factory() as session:
            results = await get_lookup_registry().run_all(input_data.case_id, session)

        warnings: list[str] = []
        if all(
            r.status_badge == "chua_xac_thuc" and not r.data.get("raw_findings") for r in results
        ):
            warnings.append(
                f"Chưa có dữ liệu tra cứu cho hồ sơ '{input_data.case_id}' "
                "— kiểm tra case_id hoặc chạy bước tra cứu."
            )

        return PropertyLookupOutput(
            case_id=input_data.case_id,
            findings=[_to_finding(r) for r in results],
            market_comparables=_to_comparables(results),
            warnings=warnings,
        )
