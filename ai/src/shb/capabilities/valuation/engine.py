"""PAA valuation engine — deterministic property valuation from Màn 1 + Màn 2.

Pure functions (no DB, no LLM) implementing docs/valuation-methodology.md §1–5:
sales-comparison, hedonic and cost methods, weighted blend, and the 5-factor
confidence score. The only subjective input is ``adj_llm`` (hướng nhà/phong thủy),
supplied by the caller, **bounded to ±config.adj_llm_bound**, and defaulting to 0
so results are fully reproducible from the formula (audit invariant).

Inputs are plain dataclasses so the math is unit-testable with exact numbers; the
plugin builds them from DB rows and maps fuzzy fields via ``config`` categorizers.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from shb.capabilities.valuation.config import (
    DEFAULT_CONFIG,
    RoadCategory,
    StructureCategory,
    ValuationConfig,
    badge_score,
)


class NoComparablesError(ValueError):
    """Raised when there are no comparables to anchor a market price."""


@dataclass
class Subject:
    """The property being valued (from Màn 1 property_physical_info)."""

    land_area_sqm: float
    num_floors: int = 1
    floor_area_sqm: float | None = None
    frontage_m: float | None = None
    road_category: RoadCategory = RoadCategory.ALLEY_CAR
    structure_category: StructureCategory = StructureCategory.REINFORCED_CONCRETE
    construction_year: int | None = None
    amenity_confidence: float = 0.5  # 0..1, from Màn 2 neighborhood_amenity


@dataclass
class Comparable:
    """One comparable transaction (from Màn 2 market_comparable)."""

    price_per_sqm_vnd: float
    distance_km: float
    area_sqm: float
    months_since: float  # age of the transaction, in months


@dataclass
class ValuationContext:
    """Case-level context for confidence scoring."""

    as_of_year: int
    legal_badge: str = "chua_xac_thuc"
    planning_badge: str = "chua_xac_thuc"
    price_index_series: list[float] = field(default_factory=list)


@dataclass
class MethodResult:
    """One valuation method's output + its blend weight."""

    key: str  # valuation_method_key value
    estimated_value_vnd: int
    weight_pct: int
    contribution_value_vnd: int
    inputs: list[str]


@dataclass
class FactorResult:
    """One confidence factor (§5)."""

    key: str  # confidence_factor_key value
    weight_pct: int
    score: int


@dataclass
class ValuationComputation:
    """Full engine output — maps 1:1 to the Màn 3 output/DB tables."""

    proposed_value_vnd: int
    value_low_vnd: int
    value_high_vnd: int
    price_per_sqm_vnd: int
    confidence_pct: int
    comparable_count: int
    base_ppm: float
    adj_det: float
    adj_llm: float
    dispersion: float
    methods: list[MethodResult]
    confidence_factors: list[FactorResult]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _similarity_weight(comp: Comparable, subject: Subject, cfg: ValuationConfig) -> float:
    w_dist = 1.0 / (1.0 + comp.distance_km / cfg.dist_scale_km)
    w_area = 1.0 / (1.0 + abs(comp.area_sqm - subject.land_area_sqm) / cfg.area_scale_sqm)
    w_time = 1.0 / (1.0 + max(0.0, comp.months_since) / cfg.time_scale_months)
    return w_dist * w_area * w_time


def _base_ppm(
    comps: list[Comparable], subject: Subject, cfg: ValuationConfig
) -> tuple[float, float]:
    """Return (weighted reference price/m², average similarity weight q̄)."""
    weights = [_similarity_weight(c, subject, cfg) for c in comps]
    total = sum(weights)
    if total <= 0:
        raise NoComparablesError("comparable similarity weights sum to zero")
    ppm = sum(c.price_per_sqm_vnd * w for c, w in zip(comps, weights)) / total
    return ppm, total / len(comps)


def _adj_det(subject: Subject, age: int | None, cfg: ValuationConfig) -> float:
    a_road = cfg.a_road.get(subject.road_category, 0.0)
    a_floors = min(cfg.a_floor_max, cfg.a_floor_per_floor * max(0, subject.num_floors - 1))
    a_age = cfg.age_adjustment(age)
    a_structure = cfg.a_structure.get(subject.structure_category, 0.0)
    return _clamp(a_road + a_floors + a_age + a_structure, cfg.adj_det_min, cfg.adj_det_max)


def _hedonic_value(
    base_ppm: float, subject: Subject, age: int | None, cfg: ValuationConfig
) -> float:
    factor = (
        cfg.beta_floors * max(0, subject.num_floors - 1)
        + cfg.beta_frontage * ((subject.frontage_m or 3.0) - 3.0)
        + cfg.beta_age * max(0, (age or 0) - 10)
        + cfg.beta_amenity * (subject.amenity_confidence - 0.5)
    )
    factor = _clamp(factor, -cfg.hedonic_clamp, cfg.hedonic_clamp)
    return base_ppm * subject.land_area_sqm * (1.0 + factor)


def _cost_value(base_ppm: float, subject: Subject, age: int | None, cfg: ValuationConfig) -> float:
    land_value = subject.land_area_sqm * base_ppm  # base_ppm ≈ đơn giá đất/m²
    floor_area = subject.floor_area_sqm or 0.0
    unit_build = cfg.unit_build_cost.get(subject.structure_category, 0)
    depreciation = max(cfg.depreciation_floor, 1.0 - (age or 0) * cfg.depreciation_per_year)
    return land_value + floor_area * unit_build * depreciation


def _confidence_factors(
    n: int, qbar: float, dispersion: float, ctx: ValuationContext, cfg: ValuationConfig
) -> list[FactorResult]:
    comp_qty = round(_clamp(min(n, 6) / 6 * 60 + qbar * 40, 0, 100))
    consensus = round(_clamp(100 * (1 - dispersion), 0, 100))
    legal_planning = round((badge_score(ctx.legal_badge) + badge_score(ctx.planning_badge)) / 2)
    volatility = _volatility_score(ctx.price_index_series)
    similarity = round(_clamp(qbar * 100, 0, 100))
    return [
        FactorResult("comp_quantity_quality", cfg.cf_weight_comp_quantity, comp_qty),
        FactorResult("method_consensus", cfg.cf_weight_consensus, consensus),
        FactorResult("legal_planning_completeness", cfg.cf_weight_legal_planning, legal_planning),
        FactorResult("market_volatility", cfg.cf_weight_volatility, volatility),
        FactorResult("comp_similarity", cfg.cf_weight_similarity, similarity),
    ]


def _volatility_score(series: list[float]) -> int:
    """Score 40–100: steadier price-index series → higher (lower volatility)."""
    usable = [v for v in series if v]
    if len(usable) < 2:
        return 60
    returns = [(usable[i] - usable[i - 1]) / usable[i - 1] for i in range(1, len(usable))]
    vol = statistics.pstdev(returns) if len(returns) > 1 else abs(returns[0])
    return round(_clamp(100 - vol * 100 * 5, 40, 100))


def compute_valuation(
    subject: Subject,
    comparables: list[Comparable],
    context: ValuationContext,
    *,
    adj_llm: float = 0.0,
    config: ValuationConfig = DEFAULT_CONFIG,
) -> ValuationComputation:
    """Compute a full valuation. ``adj_llm`` (±bound) is the only subjective input.

    Raises :class:`NoComparablesError` when ``comparables`` is empty.
    """
    if not comparables:
        raise NoComparablesError("cannot value without at least one comparable")

    cfg = config
    n = len(comparables)
    base_ppm, qbar = _base_ppm(comparables, subject, cfg)
    age = (context.as_of_year - subject.construction_year) if subject.construction_year else None

    adj_det = _adj_det(subject, age, cfg)
    adj_llm = _clamp(adj_llm, -cfg.adj_llm_bound, cfg.adj_llm_bound)
    final_ppm = base_ppm * (1.0 + adj_det + adj_llm)

    value_ss = final_ppm * subject.land_area_sqm
    value_hed = _hedonic_value(base_ppm, subject, age, cfg)
    value_cost = _cost_value(base_ppm, subject, age, cfg)

    # Blend — dynamic weights; force the integer percentages to sum to 100.
    w_sales = _clamp(
        cfg.w_sales_base + cfg.w_sales_per_comp * min(n, 6), cfg.w_sales_base, cfg.w_sales_max
    )
    w_rest = 1.0 - w_sales
    w_hed = cfg.w_hedonic_share_of_rest * w_rest
    w_cost = w_rest - w_hed
    proposed = w_sales * value_ss + w_hed * value_hed + w_cost * value_cost

    values = [value_ss, value_hed, value_cost]
    mean = statistics.mean(values)
    dispersion = (statistics.pstdev(values) / mean) if mean else 0.0

    factors = _confidence_factors(n, qbar, dispersion, context, cfg)
    confidence = round(sum(f.score * f.weight_pct for f in factors) / 100)

    spread = _clamp(
        cfg.spread_base
        + cfg.spread_dispersion_k * dispersion
        + cfg.spread_confidence_k * (1 - confidence / 100),
        cfg.spread_min,
        cfg.spread_max,
    )

    w_sales_pct = round(w_sales * 100)
    w_hed_pct = round(w_hed * 100)
    w_cost_pct = 100 - w_sales_pct - w_hed_pct  # force sum = 100
    methods = [
        MethodResult(
            "sales_comparison",
            round(value_ss),
            w_sales_pct,
            round(w_sales * value_ss),
            [
                f"Giá/m² tham chiếu {round(base_ppm):,} từ {n} giao dịch (q̄={qbar:.2f})",
                f"Điều chỉnh đặc điểm (xác định): {adj_det:+.1%}",
                f"Điều chỉnh cảm tính (LLM, ±{cfg.adj_llm_bound:.0%}): {adj_llm:+.1%}",
            ],
        ),
        MethodResult(
            "hedonic_ml",
            round(value_hed),
            w_hed_pct,
            round(w_hed * value_hed),
            ["Mô hình hedonic tuyến tính trên đặc điểm định lượng (không cảm tính)"],
        ),
        MethodResult(
            "cost_approach",
            round(value_cost),
            w_cost_pct,
            round(w_cost * value_cost),
            ["Giá trị đất + chi phí xây dựng đã khấu hao theo tuổi công trình"],
        ),
    ]

    return ValuationComputation(
        proposed_value_vnd=round(proposed),
        value_low_vnd=round(proposed * (1 - spread)),
        value_high_vnd=round(proposed * (1 + spread)),
        price_per_sqm_vnd=round(proposed / subject.land_area_sqm),
        confidence_pct=confidence,
        comparable_count=n,
        base_ppm=base_ppm,
        adj_det=adj_det,
        adj_llm=adj_llm,
        dispersion=dispersion,
        methods=methods,
        confidence_factors=factors,
    )
