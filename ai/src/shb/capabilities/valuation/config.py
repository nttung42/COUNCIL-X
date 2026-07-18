"""Tunable coefficients for the PAA valuation engine.

Every number the engine uses lives here (not hard-coded in ``engine.py``) so the
business can adjust the methodology without touching logic. Values are the
defaults proposed in ``docs/valuation-methodology.md`` — review/override per SHB
policy. Also holds the fuzzy input categorizers (free-text road/structure → a
category, lookup badge → a score) that map messy inputs into the clean values the
deterministic engine consumes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class RoadCategory(StrEnum):
    """Đường/lộ giới → hệ số điều chỉnh giá (a_road)."""

    MAIN_ROAD = "main_road"  # mặt tiền đường lớn
    ALLEY_CAR = "alley_car"  # hẻm ô tô ≥ 3.5m (chuẩn)
    ALLEY_BIKE = "alley_bike"  # hẻm xe máy 2–3.5m
    ALLEY_SMALL = "alley_small"  # hẻm nhỏ < 2m


class StructureCategory(StrEnum):
    """Kết cấu công trình → hệ số + đơn giá xây dựng."""

    REINFORCED_CONCRETE = "reinforced_concrete"  # BTCT / kiên cố
    SEMI_PERMANENT = "semi_permanent"  # bán kiên cố
    LEVEL_4 = "level_4"  # nhà cấp 4


@dataclass(frozen=True)
class ValuationConfig:
    """All valuation coefficients (see docs/valuation-methodology.md §1–5)."""

    # §1.1 similarity scales
    dist_scale_km: float = 1.0
    area_scale_sqm: float = 30.0
    time_scale_months: float = 12.0

    # §1.2 sales-comparison deterministic adjustments
    a_road: dict = field(
        default_factory=lambda: {
            RoadCategory.MAIN_ROAD: 0.05,
            RoadCategory.ALLEY_CAR: 0.0,
            RoadCategory.ALLEY_BIKE: -0.04,
            RoadCategory.ALLEY_SMALL: -0.08,
        }
    )
    a_floor_per_floor: float = 0.02
    a_floor_max: float = 0.08
    # age bands: (max_age_exclusive, adjustment); last band = else
    a_age_bands: tuple = ((5, 0.03), (15, 0.0), (30, -0.05))
    a_age_else: float = -0.10
    a_structure: dict = field(
        default_factory=lambda: {
            StructureCategory.REINFORCED_CONCRETE: 0.0,
            StructureCategory.SEMI_PERMANENT: -0.03,
            StructureCategory.LEVEL_4: -0.06,
        }
    )
    adj_det_min: float = -0.20
    adj_det_max: float = 0.15

    # §1.3 subjective (LLM) bound
    adj_llm_bound: float = 0.05

    # §2 hedonic betas
    beta_floors: float = 0.015
    beta_frontage: float = 0.008
    beta_age: float = -0.004
    beta_amenity: float = 0.10
    hedonic_clamp: float = 0.15

    # §3 cost approach
    unit_build_cost: dict = field(
        default_factory=lambda: {
            StructureCategory.REINFORCED_CONCRETE: 7_000_000,
            StructureCategory.SEMI_PERMANENT: 4_500_000,
            StructureCategory.LEVEL_4: 2_500_000,
        }
    )
    depreciation_per_year: float = 0.015
    depreciation_floor: float = 0.40

    # §4 blend weights + spread
    w_sales_base: float = 0.40
    w_sales_per_comp: float = 0.05
    w_sales_max: float = 0.70
    w_hedonic_share_of_rest: float = 0.55
    spread_base: float = 0.03
    spread_dispersion_k: float = 0.5
    spread_confidence_k: float = 0.10
    spread_min: float = 0.03
    spread_max: float = 0.15

    # §5 confidence factor weights (must sum to 100)
    cf_weight_comp_quantity: int = 28
    cf_weight_consensus: int = 26
    cf_weight_legal_planning: int = 18
    cf_weight_volatility: int = 17
    cf_weight_similarity: int = 11

    def age_adjustment(self, age: int | None) -> float:
        """Return a_age for a building age using the configured bands."""
        if age is None:
            return 0.0
        for max_age, adj in self.a_age_bands:
            if age < max_age:
                return adj
        return self.a_age_else


DEFAULT_CONFIG = ValuationConfig()


# --------------------------------------------------------------------------- #
# Fuzzy input → clean category/score (used by the plugin before calling engine)
# --------------------------------------------------------------------------- #
def categorize_road(desc: str | None) -> RoadCategory:
    """Map free-text ``road_type_desc`` to a :class:`RoadCategory` (keyword)."""
    text = (desc or "").lower()
    if any(k in text for k in ("mặt tiền", "mat tien", "đường lớn", "duong lon")):
        return RoadCategory.MAIN_ROAD
    if "ô tô" in text or "o to" in text or "oto" in text:
        return RoadCategory.ALLEY_CAR
    if "xe máy" in text or "xe may" in text:
        return RoadCategory.ALLEY_BIKE
    if any(k in text for k in ("hẻm nhỏ", "hem nho", "ngõ nhỏ", "nho hep")):
        return RoadCategory.ALLEY_SMALL
    return RoadCategory.ALLEY_CAR  # neutral default


def categorize_structure(desc: str | None) -> StructureCategory:
    """Map free-text ``structure_material`` to a :class:`StructureCategory`."""
    text = (desc or "").lower()
    if any(k in text for k in ("cấp 4", "cap 4", "cấp bốn")):
        return StructureCategory.LEVEL_4
    if any(k in text for k in ("bán kiên cố", "ban kien co")):
        return StructureCategory.SEMI_PERMANENT
    return StructureCategory.REINFORCED_CONCRETE  # BTCT/kiên cố default


def badge_score(badge: str | None) -> float:
    """Map a lookup badge to a 0–100 completeness score (for confidence §5)."""
    return {"da_xac_thuc": 90.0, "luu_y": 60.0, "chua_xac_thuc": 30.0}.get(badge or "", 50.0)
