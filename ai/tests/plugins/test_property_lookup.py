"""Tests for the property_lookup plugin (Màn 2 — Kết quả tra cứu).

Seeds a case's ``lookup_finding`` + ``market_comparable`` rows into the in-memory
SQLite ``test_db`` (conftest), then drives ``PropertyLookupService.run`` end-to-end
via a session-factory ctx — the same shape the API/worker inject.
"""

from __future__ import annotations

from shb.ai.plugins.base import AIServiceContext
from shb.ai.plugins.property_lookup.schema import (
    LookupBadge,
    LookupCategory,
    PropertyLookupInput,
)
from shb.ai.plugins.property_lookup.service import PropertyLookupService
from shb.ai.plugins.registry import AIServiceRegistry
from shb.db.models_paa import (
    AppraisalCase,
)
from shb.db.models_paa import LookupBadge as DBLookupBadge
from shb.db.models_paa import LookupCategory as DBLookupCategory
from shb.db.models_paa import (
    LookupFinding,
    MarketComparable,
)

_ALL_CATEGORIES = [
    (
        DBLookupCategory.MARKET_PRICE,
        "market_price_lookup",
        "Giá thị trường",
        DBLookupBadge.DA_XAC_THUC,
        78,
    ),
    (
        DBLookupCategory.PLANNING_ZONING,
        "planning_zoning_lookup",
        "Quy hoạch",
        DBLookupBadge.DA_XAC_THUC,
        93,
    ),
    (DBLookupCategory.LEGAL_STATUS, "legal_status_lookup", "Pháp lý", DBLookupBadge.LUU_Y, 55),
    (
        DBLookupCategory.NEIGHBORHOOD_AMENITY,
        "neighborhood_amenity_lookup",
        "Tiện ích",
        DBLookupBadge.DA_XAC_THUC,
        81,
    ),
    (
        DBLookupCategory.ENVIRONMENTAL_RISK,
        "environmental_risk_lookup",
        "Môi trường",
        DBLookupBadge.LUU_Y,
        57,
    ),
    (
        DBLookupCategory.LIQUIDITY_STAT,
        "liquidity_stat_lookup",
        "Thanh khoản",
        DBLookupBadge.DA_XAC_THUC,
        94,
    ),
    (
        DBLookupCategory.STIGMA_REPUTATION,
        "stigma_reputation_lookup",
        "Dư luận",
        DBLookupBadge.CHUA_XAC_THUC,
        30,
    ),
]


async def _seed_case(session, case_id: str) -> None:
    session.add(AppraisalCase(case_id=case_id, requested_by="test"))
    for cat, tool, title, badge, conf in _ALL_CATEGORIES:
        session.add(
            LookupFinding(
                case_id=case_id,
                category=cat,
                tool_name=tool,
                status_badge=badge,
                title=title,
                raw_findings=[f"{title} — dòng 1", f"{title} — dòng 2"],
                inference_text=f"Nhận định {title}.",
                source_label=tool,
                confidence_pct=conf,
            )
        )
    session.add(
        MarketComparable(
            case_id=case_id,
            comp_address="Hẻm 40 Nguyễn Văn A",
            distance_km=0.3,
            area_sqm=58,
            price_per_sqm_vnd=76_600_000,
            display_order=0,
        )
    )
    session.add(
        MarketComparable(
            case_id=case_id,
            comp_address="Đường Lê Văn C",
            distance_km=1.1,
            area_sqm=70,
            price_per_sqm_vnd=95_000_000,
            display_order=1,
        )
    )
    await session.commit()


def _factory(session):
    """Return a db_session_factory that yields the test session without closing it."""

    class _CM:
        def __call__(self):
            return self

        async def __aenter__(self):
            return session

        async def __aexit__(self, *_exc):
            return False

    return _CM()


async def test_property_lookup_reads_case(test_db):
    """Full read: 7 findings mapped to Màn 2 shape + comparable table."""
    await _seed_case(test_db, "REQ-TEST-2000")
    ctx = AIServiceContext(
        user_id="u1", service_id="property_lookup", db_session_factory=_factory(test_db)
    )

    out = await PropertyLookupService().run(PropertyLookupInput(case_id="REQ-TEST-2000"), ctx)

    assert out.case_id == "REQ-TEST-2000"
    assert len(out.findings) == 7
    assert out.warnings == []

    by_cat = {f.category: f for f in out.findings}
    mp = by_cat[LookupCategory.MARKET_PRICE]
    assert mp.status_badge == LookupBadge.DA_XAC_THUC
    assert mp.confidence_pct == 78
    assert mp.tool_name == "market_price_lookup"
    assert mp.title == "Giá thị trường"
    assert mp.raw_findings == ["Giá thị trường — dòng 1", "Giá thị trường — dòng 2"]
    assert mp.inference_text == "Nhận định Giá thị trường."

    # Reputation kept as a low-confidence, unverified advisory badge.
    assert by_cat[LookupCategory.STIGMA_REPUTATION].status_badge == LookupBadge.CHUA_XAC_THUC
    assert by_cat[LookupCategory.LEGAL_STATUS].status_badge == LookupBadge.LUU_Y

    # Comparable-sales table surfaced from the market_price adapter.
    assert len(out.market_comparables) == 2
    first = out.market_comparables[0]
    assert first.address == "Hẻm 40 Nguyễn Văn A"
    assert first.price_per_sqm_vnd == 76_600_000


async def test_property_lookup_unknown_case_warns(test_db):
    """A case with no lookup data returns 7 unverified findings + a warning."""
    ctx = AIServiceContext(
        user_id="u1", service_id="property_lookup", db_session_factory=_factory(test_db)
    )

    out = await PropertyLookupService().run(PropertyLookupInput(case_id="REQ-NONE"), ctx)

    assert len(out.findings) == 7
    assert all(f.status_badge == LookupBadge.CHUA_XAC_THUC for f in out.findings)
    assert all(f.confidence_pct == 0 for f in out.findings)
    assert out.market_comparables == []
    assert any("Chưa có dữ liệu" in w for w in out.warnings)


async def test_property_lookup_requires_db_factory():
    """Without a db_session_factory the service fails clearly (not silently)."""
    import pytest

    ctx = AIServiceContext(user_id="u1", service_id="property_lookup")
    with pytest.raises(RuntimeError, match="db_session_factory"):
        await PropertyLookupService().run(PropertyLookupInput(case_id="X"), ctx)


def test_registry_discovers_property_lookup():
    """The plugin is auto-discovered as an async (SSE-streamed), non-file service."""
    registry = AIServiceRegistry()
    registry.discover_and_register()
    service = registry.get("property_lookup")
    assert service is not None
    assert service.meta.is_async is True
    assert service.meta.accepts_file is False


async def test_property_lookup_via_registry_platform_path(test_db):
    """Integration: run the discovered service instance exactly like the API does.

    Mirrors ``run_service``'s sync path — validate input via ``InputSchema``, build
    a ctx with ``db_session_factory``, call ``service.run`` — but on SQLite.
    """
    await _seed_case(test_db, "REQ-TEST-3000")

    registry = AIServiceRegistry()
    registry.discover_and_register()
    service = registry.get("property_lookup")

    input_data = service.InputSchema(**{"case_id": "REQ-TEST-3000"})
    ctx = AIServiceContext(
        user_id="u1", service_id="property_lookup", db_session_factory=_factory(test_db)
    )
    out = await service.run(input_data, ctx)

    assert out.case_id == "REQ-TEST-3000"
    assert len(out.findings) == 7
    assert len(out.market_comparables) == 2
    # Output round-trips through the declared OutputSchema (what the API returns).
    dumped = out.model_dump()
    assert dumped["findings"][0]["category"] in {
        "market_price",
        "planning_zoning",
        "legal_status",
        "neighborhood_amenity",
        "environmental_risk",
        "liquidity_stat",
        "stigma_reputation",
    }
