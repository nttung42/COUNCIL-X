"""property_risk AI service (async, SSE) — Màn 4 Rủi ro.

Scores asset risk for a case: reads Màn 1 (legal/physical) + Màn 2 (findings) +
Màn 3 (price index) + the LTV policy from the DB, runs the deterministic
:mod:`shb.capabilities.risk.engine`, and returns the Màn 4 output. 100% formula —
no LLM — because the score drives the LTV (money) decision.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select

from shb.ai.plugins.base import AIServiceContext, AIServiceMeta, BaseAIService
from shb.ai.plugins.property_risk.schema import (
    LtvBandOut,
    PropertyRiskInput,
    PropertyRiskOutput,
    RiskAssessmentSummary,
    RiskFlagOut,
    RiskGroupOut,
)
from shb.capabilities.risk.engine import (
    RiskFinding,
    RiskInputs,
    RiskSubject,
    compute_risk,
)
from shb.db.models_paa import (
    LookupCategory,
    LookupFinding,
    PropertyLegalInfo,
    PropertyPhysicalInfo,
    RiskLtvPolicyBand,
    ValuationPriceIndexPoint,
)

logger = logging.getLogger(__name__)


def _report(ctx, value: int) -> None:
    cb = getattr(ctx, "update_progress", None)
    if callable(cb):
        try:
            cb(value)
        except Exception:  # pragma: no cover - progress is best-effort
            logger.debug("progress callback failed", exc_info=True)


def _finding(findings: dict, category: LookupCategory) -> RiskFinding | None:
    f = findings.get(category.value)
    if f is None:
        return None
    return RiskFinding(badge=f.status_badge.value, confidence_pct=f.confidence_pct)


class PropertyRiskService(BaseAIService):
    """Score a case's asset risk (5 groups) → risk score + LTV (Màn 4)."""

    meta = AIServiceMeta(
        id="property_risk",
        name="Rủi ro tài sản",
        description=(
            "Chấm điểm rủi ro của tài sản đảm bảo (không phải rủi ro tín dụng người vay) "
            "theo 5 nhóm có trọng số từ Màn 1+2+3, ra điểm rủi ro + LTV đề xuất + flags. "
            "100% công thức, audit được, không LLM."
        ),
        version="0.1.0",
        is_async=True,
        accepts_file=False,
    )

    InputSchema = PropertyRiskInput
    OutputSchema = PropertyRiskOutput

    async def run(self, input_data: PropertyRiskInput, ctx: AIServiceContext) -> PropertyRiskOutput:
        """Read inputs, score the 5 risk groups, and assemble the Màn 4 output."""
        factory = ctx.db_session_factory
        if factory is None:
            raise RuntimeError("property_risk requires ctx.db_session_factory.")
        case_id = input_data.case_id

        async with factory() as session:
            legal_info = await session.get(PropertyLegalInfo, case_id)
            phys = await session.get(PropertyPhysicalInfo, case_id)
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
            bands = list(
                (
                    await session.execute(select(RiskLtvPolicyBand).order_by(RiskLtvPolicyBand.id))
                ).scalars()
            )
        _report(ctx, 50)

        ltv_bands_out = [
            LtvBandOut(
                min_score=b.min_score,
                max_score=b.max_score,
                max_ltv_pct=b.max_ltv_pct,
                label=b.label,
            )
            for b in bands
        ]

        if phys is None and legal_info is None:
            return PropertyRiskOutput(
                case_id=case_id,
                ltv_policy_bands=ltv_bands_out,
                warnings=[f"Chưa có dữ liệu tài sản (Màn 1) cho hồ sơ '{case_id}' để chấm rủi ro."],
            )

        as_of = datetime.now(UTC).year
        inputs = RiskInputs(
            as_of_year=as_of,
            subject=RiskSubject(
                mortgage_status=getattr(legal_info, "current_mortgage_status", None),
                ownership_form=getattr(legal_info, "ownership_form", None),
                construction_year=getattr(phys, "construction_year", None),
            ),
            legal=_finding(findings, LookupCategory.LEGAL_STATUS),
            liquidity=_finding(findings, LookupCategory.LIQUIDITY_STAT),
            environmental=_finding(findings, LookupCategory.ENVIRONMENTAL_RISK),
            reputation=_finding(findings, LookupCategory.STIGMA_REPUTATION),
            price_index_series=[float(p.index_value) for p in index_rows],
        )

        # Engine uses the live LTV policy from the DB (falls back to config default).
        engine_bands = [(b.min_score, b.max_score, b.max_ltv_pct) for b in bands] or None
        comp = compute_risk(inputs, ltv_bands=engine_bands)

        warnings = []
        if not findings:
            warnings.append(
                "Chưa có dữ liệu tra cứu (Màn 2) — điểm rủi ro dùng mặc định trung bình."
            )

        output = PropertyRiskOutput(
            case_id=case_id,
            assessment=RiskAssessmentSummary(
                risk_score=comp.risk_score,
                risk_label=comp.risk_label,
                ltv_proposed_pct=comp.ltv_proposed_pct,
                risk_inference_text=comp.inference_text,
            ),
            groups=[
                RiskGroupOut(
                    group_key=g.key,
                    label=g.label,
                    weight_pct=g.weight_pct,
                    score=g.score,
                    signals=g.signals,
                    source_confidence=g.source_confidence,
                    verified=g.source_verified,
                )
                for g in comp.groups
            ],
            flags=[
                RiskFlagOut(
                    severity=f.severity,
                    title=f.title,
                    description=f.description,
                    confidence_pct=f.confidence_pct,
                    verified=f.verified,
                )
                for f in comp.flags
            ],
            ltv_policy_bands=ltv_bands_out,
            warnings=warnings,
        )
        _report(ctx, 100)
        return output
