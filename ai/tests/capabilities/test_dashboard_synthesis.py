"""Exact-arithmetic tests for the deterministic Màn 5 synthesis engine.

Values are chosen so max_loan and every verdict transition are hand-computable,
pinning docs/dashboard-methodology.md to the number.
"""

from __future__ import annotations

from shb.capabilities.dashboard.synthesis import (
    SynthesisInputs,
    VerdictFlag,
    compute_verdict,
    max_loan_vnd,
)

VALUE = 4_000_000_000


def _legal(severity: str, verified: bool) -> VerdictFlag:
    return VerdictFlag(group_key="legal", severity=severity, verified=verified, title="Pháp lý")


def test_max_loan_rounds_to_dong():
    """max_loan = value × LTV%, rounded; missing input → None."""
    assert max_loan_vnd(VALUE, 65) == 2_600_000_000
    assert max_loan_vnd(3_333_333_333, 55) == round(3_333_333_333 * 55 / 100)  # 1_833_333_333
    assert max_loan_vnd(None, 65) is None
    assert max_loan_vnd(VALUE, None) is None


def test_base_verdicts_from_label():
    """thap/trung_binh → cho vay; cao → cân nhắc; nghiem_trong → từ chối."""
    assert compute_verdict(SynthesisInputs("thap", VALUE, 75)).decision == "de_xuat_cho_vay"
    v = compute_verdict(SynthesisInputs("trung_binh", VALUE, 65))
    assert v.decision == "de_xuat_cho_vay"
    assert v.max_loan_vnd == 2_600_000_000
    assert v.downgraded is False
    assert compute_verdict(SynthesisInputs("cao", VALUE, 55)).decision == "can_nhac"
    assert compute_verdict(SynthesisInputs("nghiem_trong", VALUE, 45)).decision == "tu_choi"


def test_verified_serious_legal_flag_downgrades_one_step():
    """A verified legal flag at severity cao drops trung_binh's verdict one step."""
    v = compute_verdict(
        SynthesisInputs("trung_binh", VALUE, 65, flags=[_legal("cao", verified=True)])
    )
    assert v.decision == "can_nhac"  # de_xuat_cho_vay → can_nhac
    assert v.downgraded is True
    assert v.max_loan_vnd == 2_600_000_000  # loan amount unaffected by the downgrade


def test_downgrade_needs_verified_serious_legal_flag():
    """Unverified, non-serious, or non-legal flags do NOT downgrade the verdict."""
    unverified = compute_verdict(
        SynthesisInputs("trung_binh", VALUE, 65, flags=[_legal("cao", verified=False)])
    )
    assert unverified.decision == "de_xuat_cho_vay" and unverified.downgraded is False

    mild = compute_verdict(
        SynthesisInputs("trung_binh", VALUE, 65, flags=[_legal("trung_binh", verified=True)])
    )
    assert mild.decision == "de_xuat_cho_vay"

    non_legal = compute_verdict(
        SynthesisInputs(
            "trung_binh",
            VALUE,
            65,
            flags=[VerdictFlag(group_key="reputation", severity="nghiem_trong", verified=True)],
        )
    )
    assert non_legal.decision == "de_xuat_cho_vay"


def test_downgrade_clamps_at_tu_choi():
    """Already-worst verdict stays tu_choi even with a serious legal flag."""
    v = compute_verdict(
        SynthesisInputs("nghiem_trong", VALUE, 45, flags=[_legal("nghiem_trong", verified=True)])
    )
    assert v.decision == "tu_choi"
    assert v.downgraded is False
    assert any("thấp nhất" in r for r in v.reasons)


def test_missing_valuation_keeps_verdict_but_no_loan():
    """No valuation/LTV → verdict still computed, max_loan None + a reason."""
    v = compute_verdict(SynthesisInputs("cao", None, None))
    assert v.decision == "can_nhac"
    assert v.max_loan_vnd is None
    assert any("Chưa đủ dữ liệu" in r for r in v.reasons)


def test_reasons_are_auditable():
    """Every verdict carries a human-readable, deterministic reason trail."""
    v = compute_verdict(
        SynthesisInputs("trung_binh", VALUE, 65, flags=[_legal("cao", verified=True)])
    )
    assert v.reasons[0].startswith("Nhãn rủi ro")
    assert any("Hạ một bậc" in r for r in v.reasons)
    assert any("Hạn mức tối đa" in r for r in v.reasons)
    assert v.headline  # non-empty display headline
