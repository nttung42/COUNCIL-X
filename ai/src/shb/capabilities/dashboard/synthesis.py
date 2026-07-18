"""PAA Màn 5 synthesis — deterministic lending verdict + max loan amount.

Pure functions (no DB, no LLM). Turn the persisted Màn 3 valuation + Màn 4 risk
into a lending verdict and the maximum loan amount. The numbers and the decision
are 100% reproducible — they drive money — so there is no randomness/LLM here.
The plugin's LLM narrator only rewords these facts into prose; it can never
change any value produced below. See docs/dashboard-methodology.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Verdict decisions, best -> worst. A "downgrade" moves one step to the right.
VERDICT_ORDER = ("de_xuat_cho_vay", "can_nhac", "tu_choi")

# Severity rank (matches SeverityLevel); "serious" = cao or above.
_SEVERITY_RANK = {"thap": 0, "trung_binh": 1, "cao": 2, "nghiem_trong": 3}


@dataclass(frozen=True)
class DashboardConfig:
    """Tunable verdict mapping (docs/dashboard-methodology.md). Adjust per policy."""

    # risk_label -> base verdict
    label_verdict: dict = field(
        default_factory=lambda: {
            "thap": "de_xuat_cho_vay",
            "trung_binh": "de_xuat_cho_vay",
            "cao": "can_nhac",
            "nghiem_trong": "tu_choi",
        }
    )
    # human headline per verdict
    verdict_headline: dict = field(
        default_factory=lambda: {
            "de_xuat_cho_vay": "Đề xuất cho vay theo mức LTV chuẩn",
            "can_nhac": "Cân nhắc — cần bổ sung hồ sơ/thẩm định thêm",
            "tu_choi": "Từ chối / chuyển thẩm định thủ công",
        }
    )
    # a verified legal flag at this severity (or worse) drops the verdict one step
    legal_downgrade_group: str = "legal"
    legal_downgrade_min_severity: str = "cao"


DEFAULT_CONFIG = DashboardConfig()


@dataclass
class VerdictFlag:
    """A Màn 4 flag reduced to the signals the verdict cares about."""

    group_key: str  # legal | liquidity | price_volatility | physical_environment | reputation
    severity: str  # thap | trung_binh | cao | nghiem_trong
    verified: bool
    title: str = ""


@dataclass
class SynthesisInputs:
    """All inputs to the verdict engine for one case."""

    risk_label: str  # thap | trung_binh | cao | nghiem_trong (from risk_assessment_result)
    proposed_value_vnd: int | None = None
    ltv_proposed_pct: int | None = None
    flags: list[VerdictFlag] = field(default_factory=list)


@dataclass
class Verdict:
    """Deterministic lending verdict — maps to the Dashboard "kết luận" block."""

    decision: str  # de_xuat_cho_vay | can_nhac | tu_choi
    headline: str
    max_loan_vnd: int | None
    reasons: list[str]
    downgraded: bool


def _is_serious(sev: str, floor: str) -> bool:
    return _SEVERITY_RANK.get(sev, -1) >= _SEVERITY_RANK.get(floor, 99)


def _downgrade(decision: str) -> str:
    """Move a verdict one step toward the worse end, clamped at the last."""
    idx = VERDICT_ORDER.index(decision)
    return VERDICT_ORDER[min(idx + 1, len(VERDICT_ORDER) - 1)]


def max_loan_vnd(proposed_value_vnd: int | None, ltv_proposed_pct: int | None) -> int | None:
    """Return the max loan = value × LTV%, rounded to the nearest đồng (None if unknown)."""
    if proposed_value_vnd is None or ltv_proposed_pct is None:
        return None
    return round(proposed_value_vnd * ltv_proposed_pct / 100)


def compute_verdict(
    inputs: SynthesisInputs, *, config: DashboardConfig = DEFAULT_CONFIG
) -> Verdict:
    """Derive the lending verdict + max loan from risk label, LTV and flags.

    100% deterministic: base verdict from ``risk_label``, dropped one step if a
    verified legal flag reaches ``cao`` or worse. Every step is recorded in
    ``reasons`` for audit.
    """
    cfg = config
    base = cfg.label_verdict.get(inputs.risk_label, "can_nhac")
    reasons = [f"Nhãn rủi ro '{inputs.risk_label}' → kết luận cơ sở '{base}'."]

    downgraded = False
    trigger = next(
        (
            f
            for f in inputs.flags
            if f.group_key == cfg.legal_downgrade_group
            and f.verified
            and _is_serious(f.severity, cfg.legal_downgrade_min_severity)
        ),
        None,
    )
    decision = base
    if trigger is not None and base != VERDICT_ORDER[-1]:
        decision = _downgrade(base)
        downgraded = True
        reasons.append(
            f"Hạ một bậc → '{decision}' do cảnh báo pháp lý đã xác thực mức "
            f"'{trigger.severity}'" + (f" ({trigger.title})." if trigger.title else ".")
        )
    elif trigger is not None:
        reasons.append(
            f"Đã có cảnh báo pháp lý xác thực mức '{trigger.severity}'; "
            "kết luận đã ở mức thấp nhất."
        )

    loan = max_loan_vnd(inputs.proposed_value_vnd, inputs.ltv_proposed_pct)
    if loan is not None:
        reasons.append(
            f"Hạn mức tối đa = {inputs.proposed_value_vnd:,} × {inputs.ltv_proposed_pct}% "
            f"= {loan:,} đồng."
        )
    else:
        reasons.append("Chưa đủ dữ liệu định giá/LTV để tính hạn mức cho vay.")

    return Verdict(
        decision=decision,
        headline=cfg.verdict_headline.get(decision, decision),
        max_loan_vnd=loan,
        reasons=reasons,
        downgraded=downgraded,
    )
