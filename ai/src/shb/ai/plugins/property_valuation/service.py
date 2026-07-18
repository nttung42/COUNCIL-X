"""property_valuation AI service (async, SSE) — Màn 3 Định giá.

Computes a transparent valuation for a case: reads the Màn 1 subject +
Màn 2 comparables/findings/price-index from the DB, runs the deterministic
:mod:`shb.capabilities.valuation.engine`, and layers ONE bounded LLM subjective
adjustment (±5%) on top — clearly separated in the output. Async so it streams
progress over the unified SSE channel.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, date, datetime

from sqlalchemy import select

from shb.ai.plugins.base import AIServiceContext, AIServiceMeta, BaseAIService
from shb.ai.plugins.property_valuation.schema import (
    ConfidenceFactorKey,
    FactorOut,
    MethodOut,
    PriceIndexPointOut,
    PropertyValuationInput,
    PropertyValuationOutput,
    SubjectiveAdjustmentOut,
    ValuationMethodKey,
    ValuationSummary,
)
from shb.capabilities.valuation.config import categorize_road, categorize_structure
from shb.capabilities.valuation.engine import (
    Comparable,
    NoComparablesError,
    Subject,
    ValuationContext,
    compute_valuation,
)
from shb.capabilities.valuation.subjective import assess_subjective_adjustment
from shb.db.models_paa import (
    LookupCategory,
    LookupFinding,
    MarketComparable,
    PropertyPhysicalInfo,
    ValuationPriceIndexPoint,
)

logger = logging.getLogger(__name__)

_FACTOR_LABEL = {
    "comp_quantity_quality": "Giao dịch so sánh (SL & chất lượng)",
    "method_consensus": "Đồng thuận giữa 3 phương pháp",
    "legal_planning_completeness": "Pháp lý & quy hoạch đầy đủ",
    "market_volatility": "Biến động thị trường gần đây",
    "comp_similarity": "Tương đồng giao dịch so sánh",
}
_METHOD_LABEL = {
    "sales_comparison": "So sánh trực tiếp",
    "hedonic_ml": "Hedonic (ML)",
    "cost_approach": "Chi phí xây dựng",
}


def _first_int(text: str | None) -> int | None:
    m = re.search(r"\d+", text or "")
    return int(m.group(0)) if m else None


def _months_since(txn: date | None, as_of: date) -> float:
    if txn is None:
        return 12.0
    return max(0.0, (as_of - txn).days / 30.44)


def _report(ctx, value: int) -> None:
    cb = getattr(ctx, "update_progress", None)
    if callable(cb):
        try:
            cb(value)
        except Exception:  # pragma: no cover - progress is best-effort
            logger.debug("progress callback failed", exc_info=True)


class PropertyValuationService(BaseAIService):
    """Compute a case's valuation (3 methods + confidence) for Màn 3."""

    meta = AIServiceMeta(
        id="property_valuation",
        name="Định giá bất động sản",
        description=(
            "Định giá tài sản theo 3 phương pháp (so sánh trực tiếp, hedonic, chi phí) "
            "từ thông tin Màn 1 + giao dịch so sánh Màn 2, kèm điểm tin cậy. Phần cảm "
            "tính (hướng nhà/phong thủy) do LLM quyết định, chặn ±5%, tách bạch rõ."
        ),
        version="0.1.0",
        is_async=True,
        accepts_file=False,
    )

    InputSchema = PropertyValuationInput
    OutputSchema = PropertyValuationOutput

    async def run(
        self, input_data: PropertyValuationInput, ctx: AIServiceContext
    ) -> PropertyValuationOutput:
        """Read inputs, compute the valuation, and assemble the Màn 3 output."""
        factory = ctx.db_session_factory
        if factory is None:
            raise RuntimeError("property_valuation requires ctx.db_session_factory.")
        case_id = input_data.case_id

        async with factory() as session:
            subject_row = await session.get(PropertyPhysicalInfo, case_id)
            comps_rows = list(
                (
                    await session.execute(
                        select(MarketComparable)
                        .where(MarketComparable.case_id == case_id)
                        .order_by(MarketComparable.display_order)
                    )
                ).scalars()
            )
            findings = {
                f.category.value: f
                for f in (
                    await session.execute(
                        select(LookupFinding).where(LookupFinding.case_id == case_id)
                    )
                ).scalars()
            }
            index_rows = list(
                (
                    await session.execute(
                        select(ValuationPriceIndexPoint)
                        .where(ValuationPriceIndexPoint.case_id == case_id)
                        .order_by(ValuationPriceIndexPoint.display_order)
                    )
                ).scalars()
            )
        _report(ctx, 40)

        if subject_row is None or not comps_rows:
            missing = (
                "thông tin tài sản (Màn 1)" if subject_row is None else "giao dịch so sánh (Màn 2)"
            )
            return PropertyValuationOutput(
                case_id=case_id,
                price_index_series=_index_series(index_rows),
                warnings=[f"Chưa đủ dữ liệu để định giá hồ sơ '{case_id}': thiếu {missing}."],
            )

        as_of = datetime.now(UTC).date()
        subject = _build_subject(subject_row, findings)
        comparables = [
            Comparable(
                price_per_sqm_vnd=float(c.price_per_sqm_vnd),
                distance_km=float(c.distance_km or 0),
                area_sqm=float(c.area_sqm or subject.land_area_sqm),
                months_since=_months_since(c.transaction_date, as_of),
            )
            for c in comps_rows
        ]
        context = ValuationContext(
            as_of_year=as_of.year,
            legal_badge=_badge(findings, LookupCategory.LEGAL_STATUS),
            planning_badge=_badge(findings, LookupCategory.PLANNING_ZONING),
            price_index_series=[float(p.index_value) for p in index_rows],
        )

        # Single subjective (LLM) input — bounded ±5%, fail-safe to 0.
        adj_llm, reason = await assess_subjective_adjustment(
            {
                "hướng nhà": subject_row.house_direction,
                "địa chỉ": subject_row.address,
                "loại đường/hẻm": subject_row.road_type_desc,
                "kết cấu": subject_row.structure_material,
                "hiện trạng": subject_row.current_usage_status,
            }
        )
        _report(ctx, 75)

        try:
            comp = compute_valuation(subject, comparables, context, adj_llm=adj_llm)
        except NoComparablesError:
            return PropertyValuationOutput(
                case_id=case_id,
                price_index_series=_index_series(index_rows),
                warnings=[
                    f"Không định giá được hồ sơ '{case_id}': giao dịch so sánh không hợp lệ."
                ],
            )

        output = _assemble(case_id, comp, reason, index_rows)
        _report(ctx, 100)
        return output


def _badge(findings: dict, category: LookupCategory) -> str:
    f = findings.get(category.value)
    return f.status_badge.value if f else "chua_xac_thuc"


def _build_subject(row: PropertyPhysicalInfo, findings: dict) -> Subject:
    amenity = findings.get(LookupCategory.NEIGHBORHOOD_AMENITY.value)
    amenity_conf = (amenity.confidence_pct / 100.0) if amenity and amenity.confidence_pct else 0.5
    return Subject(
        land_area_sqm=float(row.land_area_sqm),
        num_floors=_first_int(row.num_floors_desc) or 1,
        floor_area_sqm=float(row.floor_area_sqm) if row.floor_area_sqm is not None else None,
        frontage_m=float(row.frontage_m) if row.frontage_m is not None else None,
        road_category=categorize_road(row.road_type_desc),
        structure_category=categorize_structure(row.structure_material),
        construction_year=row.construction_year,
        amenity_confidence=amenity_conf,
    )


def _index_series(rows) -> list[PriceIndexPointOut]:
    return [
        PriceIndexPointOut(
            period_label=p.period_label,
            index_value=float(p.index_value),
            display_order=p.display_order,
        )
        for p in rows
    ]


def _assemble(case_id, comp, subjective_reason, index_rows) -> PropertyValuationOutput:
    factors = [
        FactorOut(
            factor_key=ConfidenceFactorKey(f.key),
            label=_FACTOR_LABEL.get(f.key, f.key),
            weight_pct=f.weight_pct,
            score=f.score,
        )
        for f in comp.confidence_factors
    ]
    methods = [
        MethodOut(
            method_key=ValuationMethodKey(m.key),
            estimated_value_vnd=m.estimated_value_vnd,
            weight_pct=m.weight_pct,
            contribution_value_vnd=m.contribution_value_vnd,
            inputs=m.inputs,
            source_label=_METHOD_LABEL.get(m.key),
        )
        for m in comp.methods
    ]
    consensus = next(
        (f.score for f in comp.confidence_factors if f.key == "method_consensus"), None
    )
    last = index_rows[-1] if index_rows else None
    summary = ValuationSummary(
        proposed_value_vnd=comp.proposed_value_vnd,
        value_range_low_vnd=comp.value_low_vnd,
        value_range_high_vnd=comp.value_high_vnd,
        price_per_sqm_vnd=comp.price_per_sqm_vnd,
        confidence_pct=comp.confidence_pct,
        comparable_count=comp.comparable_count,
        price_index_period=last.period_label if last else None,
        price_index_value=float(last.index_value) if last else None,
        price_index_base=100,
        confidence_inference_text=(
            f"Độ tin cậy tổng {comp.confidence_pct}% là trung bình có trọng số của 5 yếu tố; "
            f"độ hội tụ giữa 3 phương pháp ở mức {consensus}%."
        ),
    )
    return PropertyValuationOutput(
        case_id=case_id,
        valuation=summary,
        methods=methods,
        confidence_factors=factors,
        price_index_series=_index_series(index_rows),
        subjective_adjustment=SubjectiveAdjustmentOut(
            value_pct=round(comp.adj_llm * 100, 2), reason=subjective_reason
        ),
        warnings=[],
    )
