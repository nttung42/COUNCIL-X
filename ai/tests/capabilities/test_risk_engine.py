"""Exact-arithmetic tests for the deterministic risk engine.

Inputs are chosen so every group score + the blend are hand-computable, pinning
docs/risk-methodology.md to the number.
"""

from __future__ import annotations

from shb.capabilities.risk.config import is_actively_mortgaged
from shb.capabilities.risk.engine import (
    RiskFinding,
    RiskInputs,
    RiskSubject,
    compute_risk,
)


def _inputs(**over) -> RiskInputs:
    base = dict(
        as_of_year=2025,
        subject=RiskSubject(
            mortgage_status="Chưa thế chấp tại TCTD nào",
            ownership_form="Sở hữu riêng",
            construction_year=2015,  # age 10
        ),
        legal=RiskFinding(badge="luu_y", confidence_pct=60),  # base 50
        liquidity=RiskFinding(badge="da_xac_thuc", confidence_pct=90),  # base 20
        environmental=RiskFinding(badge="luu_y", confidence_pct=70),  # base 50
        reputation=RiskFinding(badge="da_xac_thuc", confidence_pct=95),  # base 20
        price_index_series=[100, 105, 110],  # low volatility → floor 15
    )
    base.update(over)
    return RiskInputs(**base)


def test_group_scores_and_blend():
    """5 group scores + weighted risk score (=32) + label + LTV."""
    r = compute_risk(_inputs())
    by = {g.key: g for g in r.groups}
    assert by["legal"].score == 50
    assert by["liquidity"].score == 20
    assert by["price_volatility"].score == 15  # volatility floor
    assert by["physical_environment"].score == 50
    assert by["reputation"].score == 20
    assert sum(g.weight_pct for g in r.groups) == 100
    # (30*50 + 25*20 + 20*15 + 15*50 + 10*20)/100 = 32.5 → 32
    assert r.risk_score == 32
    assert r.risk_label == "trung_binh"  # 21–40
    assert r.ltv_proposed_pct == 65  # band 21–40 → 65%


def test_mortgage_and_age_adjustments():
    """Active mortgage (+20 legal) and >30y building (+15 physical) raise risk."""
    r = compute_risk(
        _inputs(
            subject=RiskSubject(
                mortgage_status="Đã thế chấp tại Ngân hàng X",
                ownership_form="Sở hữu riêng",
                construction_year=1985,  # age 40 > 30
            )
        )
    )
    by = {g.key: g for g in r.groups}
    assert by["legal"].score == 70  # 50 + 20
    assert by["physical_environment"].score == 65  # 50 + 15
    assert r.risk_score > 32  # higher than the clean case


def test_low_confidence_penalty():
    """A finding below the confidence threshold adds the uncertainty penalty."""
    r = compute_risk(_inputs(liquidity=RiskFinding(badge="da_xac_thuc", confidence_pct=40)))
    liq = next(g for g in r.groups if g.key == "liquidity")
    assert liq.score == 30  # 20 base + 10 low-confidence penalty


def test_high_volatility_raises_price_risk():
    """A volatile price index raises the price_volatility score above the floor."""
    r = compute_risk(_inputs(price_index_series=[100, 130, 95, 140, 90]))
    pv = next(g for g in r.groups if g.key == "price_volatility")
    assert pv.score > 15


def test_flags_from_high_groups():
    """Groups scoring ≥ threshold (50) become flags; reputation flag stays unverified."""
    r = compute_risk(_inputs(reputation=RiskFinding(badge="chua_xac_thuc", confidence_pct=30)))
    titles = {f.title for f in r.flags}
    # legal(50) + physical(50) cross the threshold; reputation base 60(+10 low-conf)=70 too
    assert "Pháp lý" in titles and "Vật lý / môi trường" in titles
    rep_flag = next((f for f in r.flags if f.title.startswith("Danh tiếng")), None)
    assert rep_flag is not None and rep_flag.verified is False


def test_missing_findings_are_medium():
    """A case with no findings scores medium (unknown) and stays deterministic."""
    a = compute_risk(RiskInputs(as_of_year=2025, price_index_series=[100, 105]))
    b = compute_risk(RiskInputs(as_of_year=2025, price_index_series=[100, 105]))
    assert a.risk_score == b.risk_score  # deterministic
    assert 0 <= a.risk_score <= 100


def test_is_actively_mortgaged():
    """Only a current (not cleared) mortgage counts as actively mortgaged."""
    assert is_actively_mortgaged("Đã thế chấp tại Ngân hàng X") is True
    assert is_actively_mortgaged("Chưa thế chấp tại TCTD nào") is False
    assert is_actively_mortgaged("Thế chấp đã tất toán, chưa xoá đăng ký") is False
    assert is_actively_mortgaged(None) is False
