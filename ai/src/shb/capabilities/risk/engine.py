"""PAA risk engine — deterministic asset-risk scoring (docs/risk-methodology.md).

Pure functions (no DB, no LLM) scoring the 5 risk groups from Màn 2 findings +
Màn 1 + Màn 3 signals, blending them into an asset risk score (0–100, higher =
riskier), mapping to a risk label + LTV band, and emitting the "flags cần lưu ý".
100% reproducible — the score drives LTV (money), so no randomness/LLM.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from shb.capabilities.risk.config import (
    DEFAULT_CONFIG,
    RiskConfig,
    group_label,
    is_actively_mortgaged,
)


@dataclass
class RiskFinding:
    """One Màn 2 lookup finding reduced to its risk signals."""

    badge: str = "chua_xac_thuc"  # da_xac_thuc | luu_y | chua_xac_thuc
    confidence_pct: int | None = None


@dataclass
class RiskSubject:
    """Màn 1 structured signals affecting risk."""

    mortgage_status: str | None = None
    ownership_form: str | None = None
    construction_year: int | None = None


@dataclass
class RiskInputs:
    """All inputs to the risk engine for one case."""

    as_of_year: int
    subject: RiskSubject = field(default_factory=RiskSubject)
    legal: RiskFinding | None = None
    liquidity: RiskFinding | None = None
    environmental: RiskFinding | None = None
    reputation: RiskFinding | None = None
    price_index_series: list[float] = field(default_factory=list)


@dataclass
class GroupScore:
    """One weighted risk group + how its score was built (audit)."""

    key: str
    label: str
    weight_pct: int
    score: int
    signals: list[str]
    source_confidence: int | None = None
    source_verified: bool = False


@dataclass
class RiskFlagOut:
    """One "flag cần lưu ý"."""

    severity: str  # thap | trung_binh | cao | nghiem_trong
    title: str
    description: str
    confidence_pct: int | None
    verified: bool


@dataclass
class RiskComputation:
    """Full engine output — maps to the Màn 4 tables."""

    risk_score: int
    risk_label: str
    ltv_proposed_pct: int
    inference_text: str
    groups: list[GroupScore]
    flags: list[RiskFlagOut]


_FLAG_DESC = {
    "legal": "Rủi ro pháp lý — kiểm tra tình trạng thế chấp/tranh chấp trước khi hoàn tất.",
    "liquidity": "Thanh khoản khu vực ở mức cần lưu ý — cân nhắc khi xác định LTV.",
    "price_volatility": "Biến động giá thị trường ở mức đáng chú ý.",
    "physical_environment": "Rủi ro vật lý/môi trường (ngập, tuổi công trình).",
    "reputation": "Tin đồn/tâm linh chưa xác thực — chỉ cảnh báo tham khảo, không dùng để từ chối.",
}


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _base_risk(finding: RiskFinding | None, cfg: RiskConfig) -> int:
    if finding is None:
        return cfg.missing_finding_risk
    base = cfg.badge_risk_base.get(finding.badge, cfg.missing_finding_risk)
    if finding.confidence_pct is not None and finding.confidence_pct < cfg.low_confidence_threshold:
        base += cfg.low_confidence_penalty
    return int(_clamp(base, 0, 100))


def _volatility_risk(series: list[float], cfg: RiskConfig) -> int:
    usable = [v for v in series if v]
    if len(usable) < 2:
        return cfg.missing_finding_risk
    rets = [(usable[i] - usable[i - 1]) / usable[i - 1] for i in range(1, len(usable))]
    vol = statistics.pstdev(rets) if len(rets) > 1 else abs(rets[0])
    return int(_clamp(round(vol * 100 * cfg.volatility_multiplier), cfg.volatility_risk_floor, 100))


def _ownership_not_sole(ownership_form: str | None) -> bool:
    text = (ownership_form or "").lower()
    if not text:
        return False
    return "riêng" not in text and "chính chủ" not in text


def compute_risk(
    inputs: RiskInputs, *, ltv_bands=None, config: RiskConfig = DEFAULT_CONFIG
) -> RiskComputation:
    """Score the 5 risk groups, blend into a risk score, and map to LTV + flags."""
    cfg = config
    sub = inputs.subject
    age = (inputs.as_of_year - sub.construction_year) if sub.construction_year else None

    # --- group scores -----------------------------------------------------
    legal_signals = [f"Nền theo tình trạng pháp lý (Màn 2): {_base_risk(inputs.legal, cfg)}"]
    legal = _base_risk(inputs.legal, cfg)
    if is_actively_mortgaged(sub.mortgage_status):
        legal += cfg.mortgage_active_add
        legal_signals.append(f"+{cfg.mortgage_active_add} đang thế chấp")
    if _ownership_not_sole(sub.ownership_form):
        legal += cfg.ownership_not_sole_add
        legal_signals.append(f"+{cfg.ownership_not_sole_add} sở hữu không riêng")
    legal = int(_clamp(legal, 0, 100))

    physical = _base_risk(inputs.environmental, cfg)
    physical_signals = [f"Nền theo môi trường (Màn 2): {physical}"]
    if age is not None and age > cfg.old_building_age:
        physical += cfg.old_building_add
        physical_signals.append(f"+{cfg.old_building_add} công trình {age} năm tuổi")
    physical = int(_clamp(physical, 0, 100))

    price_vol = _volatility_risk(inputs.price_index_series, cfg)

    groups = [
        GroupScore(
            "legal",
            group_label("legal"),
            cfg.w_legal,
            legal,
            legal_signals,
            _conf(inputs.legal),
            _verified(inputs.legal),
        ),
        GroupScore(
            "liquidity",
            group_label("liquidity"),
            cfg.w_liquidity,
            _base_risk(inputs.liquidity, cfg),
            ["Nền theo thanh khoản (Màn 2)"],
            _conf(inputs.liquidity),
            _verified(inputs.liquidity),
        ),
        GroupScore(
            "price_volatility",
            group_label("price_volatility"),
            cfg.w_price_volatility,
            price_vol,
            ["Độ biến động chuỗi chỉ số giá (Màn 3)"],
            None,
            True,
        ),
        GroupScore(
            "physical_environment",
            group_label("physical_environment"),
            cfg.w_physical_environment,
            physical,
            physical_signals,
            _conf(inputs.environmental),
            _verified(inputs.environmental),
        ),
        GroupScore(
            "reputation",
            group_label("reputation"),
            cfg.w_reputation,
            _base_risk(inputs.reputation, cfg),
            ["Nền theo dư luận/tâm linh (Màn 2)"],
            _conf(inputs.reputation),
            _verified(inputs.reputation),
        ),
    ]

    # --- blend + LTV ------------------------------------------------------
    risk_score = round(sum(g.weight_pct * g.score for g in groups) / 100)
    risk_label = cfg.risk_label(risk_score)
    ltv = cfg.ltv_for_score(risk_score, ltv_bands)

    # --- flags ------------------------------------------------------------
    flags = [
        RiskFlagOut(
            severity=cfg.risk_label(g.score),
            title=g.label,
            description=_FLAG_DESC.get(g.key, g.label),
            confidence_pct=g.source_confidence,
            verified=g.source_verified,
        )
        for g in sorted(groups, key=lambda x: x.score, reverse=True)
        if g.score >= cfg.flag_threshold
    ]

    top = max(groups, key=lambda g: g.score)
    inference = (
        f"Điểm rủi ro tài sản {risk_score}/100 ({risk_label}). "
        f"LTV đề xuất tối đa {ltv}%. Nhóm rủi ro cao nhất: {top.label} ({top.score})."
    )

    return RiskComputation(risk_score, risk_label, ltv, inference, groups, flags)


def _conf(f: RiskFinding | None) -> int | None:
    return f.confidence_pct if f else None


def _verified(f: RiskFinding | None) -> bool:
    return bool(f and f.badge == "da_xac_thuc")
