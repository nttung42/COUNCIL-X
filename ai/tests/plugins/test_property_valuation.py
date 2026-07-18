"""Tests for the property_valuation plugin (Màn 3 — Định giá).

Seeds a case's Màn 1 subject + Màn 2 comparables/findings/price-index into SQLite,
mocks the LLM subjective adjustment, then drives ``PropertyValuationService.run``.
The exact valuation math is covered by ``tests/capabilities/test_valuation_engine``;
here we check the DB→engine wiring + output shape.
"""

from __future__ import annotations

from datetime import date

from shb.ai.plugins.base import AIServiceContext
from shb.ai.plugins.property_valuation import service as val_service
from shb.ai.plugins.property_valuation.schema import (
    ConfidenceFactorKey,
    PropertyValuationInput,
    ValuationMethodKey,
)
from shb.ai.plugins.property_valuation.service import PropertyValuationService
from shb.ai.plugins.registry import AIServiceRegistry
from shb.capabilities.valuation.subjective import assess_subjective_adjustment
from shb.db.models_paa import (
    AppraisalCase,
    LookupBadge,
    LookupCategory,
    LookupFinding,
    MarketComparable,
    PropertyPhysicalInfo,
    ValuationPriceIndexPoint,
)


async def _seed(session, case_id: str) -> None:
    session.add(AppraisalCase(case_id=case_id, requested_by="test"))
    session.add(
        PropertyPhysicalInfo(
            case_id=case_id,
            address="123 Lê Lợi, Q1",
            property_type="Nhà phố",
            land_area_sqm=60,
            floor_area_sqm=120,
            num_floors_desc="2 tầng",
            frontage_m=4,
            road_type_desc="Hẻm bê tông, ô tô vào được",
            structure_material="Bê tông cốt thép",
            construction_year=2015,
            house_direction="Đông Nam",
        )
    )
    for i, (ppm, dist) in enumerate([(100_000_000, 0.0), (120_000_000, 1.0)]):
        session.add(
            MarketComparable(
                case_id=case_id,
                comp_address=f"Comp {i}",
                distance_km=dist,
                area_sqm=60,
                transaction_date=date(2026, 6, 1),
                price_per_sqm_vnd=ppm,
                display_order=i,
            )
        )
    for cat, badge, conf in [
        (LookupCategory.LEGAL_STATUS, LookupBadge.DA_XAC_THUC, 90),
        (LookupCategory.PLANNING_ZONING, LookupBadge.DA_XAC_THUC, 88),
        (LookupCategory.NEIGHBORHOOD_AMENITY, LookupBadge.DA_XAC_THUC, 80),
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
    for i, idx in enumerate([100, 105, 110, 115, 118, 120]):
        session.add(
            ValuationPriceIndexPoint(
                case_id=case_id, period_label=f"2025-Q{i+1}", index_value=idx, display_order=i
            )
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


def _mock_subjective(monkeypatch, fraction=0.02, reason="Hướng Đông Nam thoáng"):
    async def _fake(_features, **_kw):
        return fraction, reason

    monkeypatch.setattr(val_service, "assess_subjective_adjustment", _fake)


async def test_valuation_full(test_db, monkeypatch):
    """Full compute: valuation summary + 3 methods + 5 factors + subjective block."""
    await _seed(test_db, "REQ-VAL-1")
    _mock_subjective(monkeypatch, fraction=0.02)
    ctx = AIServiceContext(
        user_id="u1", service_id="property_valuation", db_session_factory=_factory(test_db)
    )

    out = await PropertyValuationService().run(PropertyValuationInput(case_id="REQ-VAL-1"), ctx)

    assert out.case_id == "REQ-VAL-1"
    assert out.valuation is not None
    v = out.valuation
    assert v.proposed_value_vnd > 0
    assert v.value_range_low_vnd < v.proposed_value_vnd < v.value_range_high_vnd
    assert v.comparable_count == 2
    assert 0 <= v.confidence_pct <= 100
    assert v.price_index_period == "2025-Q6" and v.price_index_value == 120

    # 3 methods, weights sum to 100
    assert {m.method_key for m in out.methods} == {
        ValuationMethodKey.SALES_COMPARISON,
        ValuationMethodKey.HEDONIC_ML,
        ValuationMethodKey.COST_APPROACH,
    }
    assert sum(m.weight_pct for m in out.methods) == 100

    # 5 confidence factors with labels
    assert {f.factor_key for f in out.confidence_factors} == set(ConfidenceFactorKey)
    assert all(f.label for f in out.confidence_factors)

    # subjective block is explicit + separable
    assert out.subjective_adjustment is not None
    assert out.subjective_adjustment.value_pct == 2.0  # 0.02 → 2%
    assert out.subjective_adjustment.source == "llm_inference"
    assert out.subjective_adjustment.bound_pct == 5.0
    assert len(out.price_index_series) == 6


async def test_valuation_no_data_warns(test_db, monkeypatch):
    """A case with no subject/comparables returns no valuation + a warning."""
    _mock_subjective(monkeypatch)
    ctx = AIServiceContext(
        user_id="u1", service_id="property_valuation", db_session_factory=_factory(test_db)
    )
    out = await PropertyValuationService().run(PropertyValuationInput(case_id="REQ-NONE"), ctx)
    assert out.valuation is None
    assert any("Chưa đủ dữ liệu" in w for w in out.warnings)


async def test_registry_discovers_property_valuation():
    """The plugin is auto-discovered as an async service."""
    registry = AIServiceRegistry()
    registry.discover_and_register()
    service = registry.get("property_valuation")
    assert service is not None
    assert service.meta.is_async is True


# --------------------------------------------------------------------------- #
# Subjective adjustment (LLM) — bounded + fail-safe
# --------------------------------------------------------------------------- #
class _FakeAssessor:
    def __init__(self, pct):
        self._pct = pct

    async def ainvoke(self, _messages):
        from shb.capabilities.valuation.subjective import SubjectiveAssessment

        return SubjectiveAssessment(adjustment_pct=self._pct, reason="test")


async def test_subjective_is_bounded():
    """LLM % beyond ±5 is clamped to the ±0.05 fraction."""
    frac, _ = await assess_subjective_adjustment({"hướng nhà": "Nam"}, assessor=_FakeAssessor(8.0))
    assert frac == 0.05
    frac, _ = await assess_subjective_adjustment({"hướng nhà": "Bắc"}, assessor=_FakeAssessor(-9.0))
    assert frac == -0.05


async def test_subjective_fail_safe():
    """An assessor error yields 0.0 (formula-only valuation stands)."""

    class _Boom:
        async def ainvoke(self, _messages):
            raise RuntimeError("model down")

    frac, reason = await assess_subjective_adjustment({"x": "y"}, assessor=_Boom())
    assert frac == 0.0
    assert "0%" in reason or "cảm tính" in reason
