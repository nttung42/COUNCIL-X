"""Exact-arithmetic tests for the deterministic valuation engine.

Inputs are chosen so every intermediate is hand-computable (see comments), which
pins the formulas in docs/valuation-methodology.md down to the number.
"""

from __future__ import annotations

import pytest

from shb.capabilities.valuation.config import (
    RoadCategory,
    StructureCategory,
    badge_score,
    categorize_road,
    categorize_structure,
)
from shb.capabilities.valuation.engine import (
    Comparable,
    NoComparablesError,
    Subject,
    ValuationContext,
    compute_valuation,
)


def _subject() -> Subject:
    return Subject(
        land_area_sqm=60,
        num_floors=2,
        floor_area_sqm=120,
        frontage_m=4,
        road_category=RoadCategory.ALLEY_CAR,  # a_road = 0
        structure_category=StructureCategory.REINFORCED_CONCRETE,  # a_structure = 0, build 7tr
        construction_year=2015,  # age 10 @ 2025 → a_age = 0, depreciation 0.85
        amenity_confidence=0.8,
    )


def _comps() -> list[Comparable]:
    # c1: perfectly similar (w=1); c2: 1km away (w_dist=0.5 → w=0.5)
    return [
        Comparable(price_per_sqm_vnd=100_000_000, distance_km=0, area_sqm=60, months_since=0),
        Comparable(price_per_sqm_vnd=120_000_000, distance_km=1.0, area_sqm=60, months_since=0),
    ]


def _context() -> ValuationContext:
    return ValuationContext(
        as_of_year=2025,
        legal_badge="da_xac_thuc",  # 90
        planning_badge="da_xac_thuc",  # 90
        price_index_series=[100, 105, 110],  # steady → high volatility score
    )


# --------------------------------------------------------------------------- #
# Deterministic core (adj_llm = 0)
# --------------------------------------------------------------------------- #
def test_base_ppm_and_adjustment():
    """base_ppm = weighted mean of comps; adj_det from floors only (=0.02)."""
    r = compute_valuation(_subject(), _comps(), _context())
    # (100M*1 + 120M*0.5) / 1.5 = 160M/1.5
    assert r.base_ppm == pytest.approx(160_000_000 / 1.5)
    assert r.adj_det == pytest.approx(0.02)  # +0.02 for the 2nd floor
    assert r.adj_llm == 0.0


def test_method_values_and_weights():
    """Each method value + the blend weights (50/28/22) match the formula."""
    r = compute_valuation(_subject(), _comps(), _context())
    by = {m.key: m for m in r.methods}

    # sales: final_ppm = base*(1+0.02) = 108.8M ; ×60 = 6.528 tỷ
    assert by["sales_comparison"].estimated_value_vnd == pytest.approx(6_528_000_000, abs=10)
    # hedonic factor = 0.015 + 0.008 + 0 + 0.10*0.3 = 0.053 ; 6.4tỷ×1.053
    assert by["hedonic_ml"].estimated_value_vnd == pytest.approx(6_739_200_000, abs=10)
    # cost: đất 6.4tỷ + sàn 120×7tr×0.85 (714tr) = 7.114 tỷ
    assert by["cost_approach"].estimated_value_vnd == pytest.approx(7_114_000_000, abs=10)

    assert by["sales_comparison"].weight_pct == 50
    assert by["hedonic_ml"].weight_pct == 28
    assert by["cost_approach"].weight_pct == 22
    assert sum(m.weight_pct for m in r.methods) == 100


def test_proposed_and_range():
    """Blended proposed value + range ordering."""
    r = compute_valuation(_subject(), _comps(), _context())
    # 0.5*6.528 + 0.275*6.7392 + 0.225*7.114 (tỷ) = 6.71793 tỷ
    assert r.proposed_value_vnd == pytest.approx(6_717_930_000, abs=50)
    assert r.value_low_vnd < r.proposed_value_vnd < r.value_high_vnd
    assert r.price_per_sqm_vnd == pytest.approx(round(r.proposed_value_vnd / 60), abs=1)
    assert r.comparable_count == 2


def test_confidence_factors_and_aggregate():
    """Exact factor scores where hand-computable; confidence = weighted sum."""
    r = compute_valuation(_subject(), _comps(), _context())
    scores = {f.key: f for f in r.confidence_factors}
    assert scores["comp_quantity_quality"].score == 50  # 2/6*60 + 0.75*40
    assert scores["legal_planning_completeness"].score == 90  # (90+90)/2
    assert scores["comp_similarity"].score == 75  # q̄=0.75
    # confidence is the exact weighted sum of the factors the engine returned.
    expected = round(sum(f.score * f.weight_pct for f in r.confidence_factors) / 100)
    assert r.confidence_pct == expected
    assert 70 <= r.confidence_pct <= 90


# --------------------------------------------------------------------------- #
# Subjective LLM adjustment (bounded, auditable)
# --------------------------------------------------------------------------- #
def test_adj_llm_is_bounded():
    """adj_llm is clamped to ±0.05 and shifts only the sales-comparison value."""
    r = compute_valuation(_subject(), _comps(), _context(), adj_llm=0.10)
    assert r.adj_llm == 0.05  # clamped from 0.10
    # final_ppm = base*(1+0.02+0.05)=base*1.07 ; ×60
    by = {m.key: m for m in r.methods}
    assert by["sales_comparison"].estimated_value_vnd == pytest.approx(
        160_000_000 / 1.5 * 1.07 * 60, abs=10
    )


def test_audit_invariant_without_llm():
    """Dropping adj_llm (=0) reproduces a purely formula-based valuation."""
    a = compute_valuation(_subject(), _comps(), _context(), adj_llm=0.0)
    b = compute_valuation(_subject(), _comps(), _context())  # default 0
    assert a.proposed_value_vnd == b.proposed_value_vnd


def test_no_comparables_raises():
    """No comparables → cannot anchor a market price."""
    with pytest.raises(NoComparablesError):
        compute_valuation(_subject(), [], _context())


# --------------------------------------------------------------------------- #
# Config categorizers
# --------------------------------------------------------------------------- #
def test_categorizers_and_badge_score():
    """Free-text road/structure map to categories; badges map to scores."""
    assert categorize_road("Hẻm bê tông, ô tô vào được") == RoadCategory.ALLEY_CAR
    assert categorize_road("Mặt tiền đường lớn") == RoadCategory.MAIN_ROAD
    assert categorize_road("Hẻm xe máy 2m") == RoadCategory.ALLEY_BIKE
    assert categorize_structure("Nhà cấp 4") == StructureCategory.LEVEL_4
    assert categorize_structure("Bê tông cốt thép") == StructureCategory.REINFORCED_CONCRETE
    assert badge_score("da_xac_thuc") == 90
    assert badge_score("chua_xac_thuc") == 30
