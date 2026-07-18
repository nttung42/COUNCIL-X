"""Tests for the property_risk plugin (Màn 4 — Rủi ro).

Seeds Màn 1 (legal/physical) + Màn 2 (findings) + Màn 3 (price index) + the LTV
policy bands into SQLite, then drives ``PropertyRiskService.run``. Exact risk math
is covered by ``tests/capabilities/test_risk_engine``; here we check DB→engine
wiring + output shape.
"""

from __future__ import annotations

from shb.ai.plugins.base import AIServiceContext
from shb.ai.plugins.property_risk.schema import PropertyRiskInput, RiskGroupKey, SeverityLevel
from shb.ai.plugins.property_risk.service import PropertyRiskService
from shb.ai.plugins.registry import AIServiceRegistry
from shb.db.models_paa import (
    AppraisalCase,
    LookupBadge,
    LookupCategory,
    LookupFinding,
    PropertyLegalInfo,
    PropertyPhysicalInfo,
    RiskLtvPolicyBand,
    ValuationPriceIndexPoint,
)


async def _seed(session, case_id: str) -> None:
    session.add(AppraisalCase(case_id=case_id, requested_by="test"))
    session.add(
        PropertyLegalInfo(
            case_id=case_id,
            certificate_type="Sổ hồng",
            certificate_number="CS 01234567",
            current_mortgage_status="Chưa thế chấp tại TCTD nào",
            ownership_form="Sở hữu riêng",
        )
    )
    session.add(
        PropertyPhysicalInfo(
            case_id=case_id,
            address="123 Lê Lợi",
            property_type="Nhà phố",
            land_area_sqm=60,
            construction_year=2015,
        )
    )
    for cat, badge, conf in [
        (LookupCategory.LEGAL_STATUS, LookupBadge.LUU_Y, 60),
        (LookupCategory.LIQUIDITY_STAT, LookupBadge.DA_XAC_THUC, 90),
        (LookupCategory.ENVIRONMENTAL_RISK, LookupBadge.LUU_Y, 70),
        (LookupCategory.STIGMA_REPUTATION, LookupBadge.DA_XAC_THUC, 95),
    ]:
        session.add(
            LookupFinding(
                case_id=case_id,
                category=cat,
                tool_name=f"{cat.value}_lookup",
                status_badge=badge,
                title=cat.value,
                raw_findings=[],
                confidence_pct=conf,
            )
        )
    for i, idx in enumerate([100, 105, 110]):
        session.add(
            ValuationPriceIndexPoint(
                case_id=case_id, period_label=f"2025-Q{i+1}", index_value=idx, display_order=i
            )
        )
    for bid, lo, hi, ltv, label in [
        (1, 0, 20, 75, "0–20"),
        (2, 21, 40, 65, "21–40"),
        (3, 41, 60, 55, "41–60"),
        (4, 61, None, 45, ">60"),
    ]:
        session.add(
            RiskLtvPolicyBand(id=bid, min_score=lo, max_score=hi, max_ltv_pct=ltv, label=label)
        )
    await session.commit()


def _factory(session):
    """Return a db_session_factory yielding the test session without closing it."""

    class _CM:
        def __call__(self):
            return self

        async def __aenter__(self):
            return session

        async def __aexit__(self, *_exc):
            return False

    return _CM()


async def test_risk_full(test_db):
    """Full scoring: risk score 32 → trung_binh → LTV 65%, 5 groups, flags, bands."""
    await _seed(test_db, "REQ-RISK-1")
    ctx = AIServiceContext(
        user_id="u1", service_id="property_risk", db_session_factory=_factory(test_db)
    )

    out = await PropertyRiskService().run(PropertyRiskInput(case_id="REQ-RISK-1"), ctx)

    a = out.assessment
    assert a is not None
    assert a.risk_score == 32  # matches the exact engine test
    assert a.risk_label == SeverityLevel.TRUNG_BINH
    assert a.ltv_proposed_pct == 65  # band 21–40 (from seeded policy)
    assert a.risk_inference_text

    assert {g.group_key for g in out.groups} == set(RiskGroupKey)
    assert sum(g.weight_pct for g in out.groups) == 100
    assert all(g.signals for g in out.groups)  # audit trail present

    # legal(50) + physical(50) cross the flag threshold
    titles = {f.title for f in out.flags}
    assert "Pháp lý" in titles and "Vật lý / môi trường" in titles

    assert len(out.ltv_policy_bands) == 4


async def test_risk_no_data_warns(test_db):
    """A case with no Màn 1 returns no assessment + a warning (bands still returned)."""
    for bid, lo, hi, ltv in [(1, 0, 20, 75), (2, 21, 40, 65)]:
        test_db.add(
            RiskLtvPolicyBand(id=bid, min_score=lo, max_score=hi, max_ltv_pct=ltv, label="x")
        )
    await test_db.commit()
    ctx = AIServiceContext(
        user_id="u1", service_id="property_risk", db_session_factory=_factory(test_db)
    )
    out = await PropertyRiskService().run(PropertyRiskInput(case_id="REQ-NONE"), ctx)
    assert out.assessment is None
    assert any("Chưa có dữ liệu" in w for w in out.warnings)
    assert len(out.ltv_policy_bands) == 2


async def test_registry_discovers_property_risk():
    """The plugin is auto-discovered as an async service."""
    registry = AIServiceRegistry()
    registry.discover_and_register()
    service = registry.get("property_risk")
    assert service is not None
    assert service.meta.is_async is True
