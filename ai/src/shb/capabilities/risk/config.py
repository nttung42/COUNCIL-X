"""Tunable coefficients for the PAA risk engine (see docs/risk-methodology.md).

All numbers the risk engine uses live here — group weights, badge→base-risk map,
structured adjustments, the volatility multiplier, the flag threshold, the
risk-label bands, and the default LTV policy bands. Defaults are the proposed
values; adjust per SHB policy without touching engine logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RiskConfig:
    """Risk-scoring coefficients (docs/risk-methodology.md §1–4)."""

    # §2 group weights (must sum to 100)
    w_legal: int = 30
    w_liquidity: int = 25
    w_price_volatility: int = 20
    w_physical_environment: int = 15
    w_reputation: int = 10

    # §1 badge → base risk + low-confidence penalty
    badge_risk_base: dict = field(
        default_factory=lambda: {"da_xac_thuc": 20, "luu_y": 50, "chua_xac_thuc": 60}
    )
    missing_finding_risk: int = 50
    low_confidence_threshold: int = 60
    low_confidence_penalty: int = 10

    # §2 structured adjustments
    mortgage_active_add: int = 20
    ownership_not_sole_add: int = 10
    old_building_age: int = 30
    old_building_add: int = 15
    volatility_multiplier: float = 6.0
    volatility_risk_floor: int = 15

    # §3 risk-label bands (upper bound inclusive; last = else) — khớp khung LTV
    label_bands: tuple = ((20, "thap"), (40, "trung_binh"), (60, "cao"))
    label_else: str = "nghiem_trong"

    # §3 default LTV policy (min_score, max_score|None, max_ltv_pct) — mirrors seed
    default_ltv_bands: tuple = ((0, 20, 75), (21, 40, 65), (41, 60, 55), (61, None, 45))

    # §4 flags
    flag_threshold: int = 50

    def risk_label(self, score: int) -> str:
        """Map a risk score to its severity label."""
        for upper, label in self.label_bands:
            if score <= upper:
                return label
        return self.label_else

    def ltv_for_score(self, score: int, bands=None) -> int:
        """Resolve max LTV% for a risk score from the policy bands."""
        for lo, hi, ltv in bands or self.default_ltv_bands:
            if score >= lo and (hi is None or score <= hi):
                return ltv
        return self.default_ltv_bands[-1][2]


DEFAULT_CONFIG = RiskConfig()

_GROUP_LABEL = {
    "legal": "Pháp lý",
    "liquidity": "Thanh khoản",
    "price_volatility": "Biến động giá",
    "physical_environment": "Vật lý / môi trường",
    "reputation": "Danh tiếng / tâm linh",
}


def group_label(key: str) -> str:
    """Return the Vietnamese display label for a risk group key."""
    return _GROUP_LABEL.get(key, key)


def is_actively_mortgaged(mortgage_status: str | None) -> bool:
    """Return True when the certificate is currently mortgaged (not cleared/none)."""
    text = (mortgage_status or "").lower()
    if not text or "chưa" in text or "tất toán" in text or "không" in text:
        return False
    return "thế chấp" in text
