"""Smoke tests for the PAA SQL-backed tool layer (`shb.capabilities.*`).

Reuses the ``test_db`` fixture from ``tests/conftest.py`` (SQLite in-memory,
``Base.metadata.create_all``) — this also doubles as a check that
``models_paa.py`` is portable to SQLite, not just Postgres.

Run with: ``pytest tests/capabilities/test_paa_tools.py -v``
"""

from __future__ import annotations

import pytest

from shb.capabilities.dashboard.queries import get_dashboard_kpi, list_case_history
from shb.capabilities.lookup.registry import get_lookup_registry
from shb.capabilities.risk.queries import get_ltv_for_score, list_ltv_policy_bands
from shb.db.models_paa import (
    AppraisalCase,
    LookupCategory,
    LookupFinding,
    MarketComparable,
    RiskAssessmentResult,
    RiskLtvPolicyBand,
    SeverityLevel,
    ValuationResult,
)


async def _seed_case(session, case_id: str = "REQ-TEST-0001") -> None:
    session.add(AppraisalCase(case_id=case_id, requested_by="test-suite"))
    session.add(
        LookupFinding(
            case_id=case_id,
            category=LookupCategory.MARKET_PRICE,
            tool_name="comparable_sales",
            title="Giao dịch so sánh khu vực",
            raw_findings=["5 giao dịch trong bán kính 1km", "Giá trung bình 95tr/m2"],
            inference_text="Mức giá khu vực ổn định trong 2 quý gần nhất.",
            source_label="Sàn giao dịch BĐS khu vực",
            confidence_pct=82,
        )
    )
    session.add(
        MarketComparable(
            case_id=case_id,
            comp_address="123 Đường ABC, Quận 1",
            distance_km=0.4,
            area_sqm=60,
            price_per_sqm_vnd=96_000_000,
            display_order=0,
        )
    )
    session.add(
        ValuationResult(
            case_id=case_id,
            proposed_value_vnd=4_850_000_000,
            value_range_low_vnd=4_600_000_000,
            value_range_high_vnd=5_100_000_000,
            confidence_pct=78,
        )
    )
    session.add(
        RiskAssessmentResult(
            case_id=case_id,
            risk_score=35,
            risk_label=SeverityLevel.TRUNG_BINH,
            ltv_proposed_pct=65,
        )
    )
    await session.commit()


@pytest.mark.asyncio
async def test_comparable_sales_adapter_reads_finding_and_comparables(test_db):
    await _seed_case(test_db)
    registry = get_lookup_registry()
    adapter = registry.get("comparable_sales")

    result = await adapter.lookup("REQ-TEST-0001", test_db)

    assert result.adapter_key == "comparable_sales"
    assert result.confidence == pytest.approx(0.82)
    assert len(result.data["comparables"]) == 1
    assert result.data["comparables"][0]["price_per_sqm_vnd"] == 96_000_000


@pytest.mark.asyncio
async def test_lookup_adapter_without_data_is_unverified(test_db):
    await _seed_case(test_db)
    registry = get_lookup_registry()
    adapter = registry.get("reputation")  # no lookup_finding row seeded for this category

    result = await adapter.lookup("REQ-TEST-0001", test_db)

    assert result.verified is False
    assert result.confidence == 0.0
    assert result.status_badge == "chua_xac_thuc"


@pytest.mark.asyncio
async def test_run_all_fans_out_seven_adapters(test_db):
    await _seed_case(test_db)
    registry = get_lookup_registry()

    results = await registry.run_all("REQ-TEST-0001", test_db)

    assert len(results) == 7
    assert {r.adapter_key for r in results} == {
        "comparable_sales",
        "zoning",
        "legal",
        "amenities",
        "environment",
        "liquidity",
        "reputation",
    }


@pytest.mark.asyncio
async def test_ltv_policy_band_resolution(test_db):
    for band in (
        RiskLtvPolicyBand(id=1, min_score=0, max_score=20, max_ltv_pct=75, label="0-20"),
        RiskLtvPolicyBand(id=2, min_score=21, max_score=40, max_ltv_pct=65, label="21-40"),
        RiskLtvPolicyBand(id=3, min_score=41, max_score=60, max_ltv_pct=55, label="41-60"),
        RiskLtvPolicyBand(id=4, min_score=61, max_score=None, max_ltv_pct=45, label=">60"),
    ):
        test_db.add(band)
    await test_db.commit()

    assert (await get_ltv_for_score(35, test_db)).max_ltv_pct == 65
    assert (await get_ltv_for_score(0, test_db)).max_ltv_pct == 75
    assert (await get_ltv_for_score(95, test_db)).max_ltv_pct == 45  # open-ended ">60" band
    assert len(await list_ltv_policy_bands(test_db)) == 4


@pytest.mark.asyncio
async def test_dashboard_kpi_and_case_history(test_db):
    await _seed_case(test_db)

    kpi = await get_dashboard_kpi("REQ-TEST-0001", test_db)
    assert kpi["proposed_value_vnd"] == 4_850_000_000
    assert kpi["risk_label"] == "trung_binh"

    history = await list_case_history(test_db)
    assert history[0]["case_id"] == "REQ-TEST-0001"
