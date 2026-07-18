"""Tests for the property_dashboard plugin (Màn 5 — Dashboard).

Seeds Màn 1 (legal/physical) + Màn 2 (findings) + Màn 3 (valuation) + Màn 4
(risk + flags) + trace into SQLite, then drives ``PropertyDashboardService.run``.
The verdict math is covered by ``tests/capabilities/test_dashboard_synthesis``;
here we check DB→engine wiring, KPI assembly and the narration fail-safe. The LLM
narrator is monkeypatched so the test runs offline and deterministically.
"""

from __future__ import annotations

import shb.ai.plugins.property_dashboard.service as dash_service
from shb.ai.plugins.base import AIServiceContext
from shb.ai.plugins.property_dashboard.schema import PropertyDashboardInput, VerdictDecision
from shb.ai.plugins.property_dashboard.service import PropertyDashboardService
from shb.ai.plugins.registry import AIServiceRegistry
from shb.capabilities.dashboard.narrator import DashboardNarration
from shb.db.models_paa import (
    AgentTraceEvent,
    AppraisalCase,
    LookupBadge,
    LookupCategory,
    LookupFinding,
    PropertyLegalInfo,
    PropertyPhysicalInfo,
    RiskAssessmentResult,
    RiskFlag,
    SeverityLevel,
    ValuationResult,
    VerificationStatus,
)


def _factory(session):
    """Return a db_session_factory yielding the test session without closing it."""

    class _CM:
        def __call__(self):
            return self

        async def __aenter__(self):
            return session

        async def __aexit__(self, *_exc):
            return False

    return _CM()


def _passthrough_narrator(monkeypatch, generated_by="llm"):
    """Replace the LLM narrator with an offline echo of the templates."""

    async def _fake(facts, *, narrator=None):
        return DashboardNarration(
            step_summaries=[(s.step_number, s.template_text) for s in facts.steps],
            overall_narrative=facts.overall_template,
            generated_by=generated_by,
        )

    monkeypatch.setattr(dash_service, "narrate_dashboard", _fake)


async def _seed(session, case_id: str, *, with_risk=True, legal_flag=False) -> None:
    session.add(AppraisalCase(case_id=case_id, requested_by="test"))
    session.add(
        PropertyPhysicalInfo(
            case_id=case_id,
            address="123 Lê Lợi",
            property_type="Nhà phố",
            land_area_sqm=60,
            construction_year=2015,
        )
    )
    session.add(
        PropertyLegalInfo(
            case_id=case_id,
            certificate_type="Sổ hồng",
            certificate_number="CS 0123",
            current_mortgage_status="Chưa thế chấp tại TCTD nào",
            ownership_form="Sở hữu riêng",
        )
    )
    session.add(
        LookupFinding(
            case_id=case_id,
            category=LookupCategory.LEGAL_STATUS,
            tool_name="legal_lookup",
            status_badge=LookupBadge.DA_XAC_THUC,
            title="Pháp lý",
            raw_findings=[],
            confidence_pct=90,
        )
    )
    session.add(
        ValuationResult(
            case_id=case_id,
            proposed_value_vnd=4_000_000_000,
            value_range_low_vnd=3_800_000_000,
            value_range_high_vnd=4_200_000_000,
            confidence_pct=82,
        )
    )
    if with_risk:
        session.add(
            RiskAssessmentResult(
                case_id=case_id,
                risk_score=32,
                risk_label=SeverityLevel.TRUNG_BINH,
                ltv_proposed_pct=65,
            )
        )
        session.add(
            RiskFlag(
                case_id=case_id,
                severity=SeverityLevel.CAO if legal_flag else SeverityLevel.TRUNG_BINH,
                title="Pháp lý" if legal_flag else "Thanh khoản",
                description="test flag",
                confidence_pct=80,
                verified_status=(
                    VerificationStatus.DA_XAC_THUC
                    if legal_flag
                    else VerificationStatus.CHUA_XAC_THUC
                ),
                display_order=0,
            )
        )
    session.add(
        AgentTraceEvent(
            case_id=case_id,
            seconds_offset=1.5,
            actor="valuation_agent",
            title="Định giá xong",
            event_order=1,
        )
    )
    await session.commit()


async def test_dashboard_full(test_db, monkeypatch):
    """Full aggregate: KPI + verdict (đề xuất cho vay) + 4 summaries + trace + history."""
    _passthrough_narrator(monkeypatch)
    await _seed(test_db, "REQ-DASH-1")
    ctx = AIServiceContext(
        user_id="u1", service_id="property_dashboard", db_session_factory=_factory(test_db)
    )

    out = await PropertyDashboardService().run(PropertyDashboardInput(case_id="REQ-DASH-1"), ctx)

    assert out.kpi is not None
    assert out.kpi.proposed_value_vnd == 4_000_000_000
    assert out.kpi.risk_score == 32 and out.kpi.ltv_proposed_pct == 65

    assert out.verdict is not None
    assert out.verdict.decision == VerdictDecision.DE_XUAT_CHO_VAY
    assert out.verdict.max_loan_vnd == 2_600_000_000  # 4e9 × 65%
    assert out.verdict.downgraded is False

    assert [s.step_number for s in out.step_summaries] == [1, 2, 3, 4]
    assert all(s.generated_by == "llm" for s in out.step_summaries)
    assert out.overall_narrative
    assert len(out.trace) == 1 and out.trace[0].actor == "valuation_agent"
    assert any(h.case_id == "REQ-DASH-1" for h in out.case_history)
    assert not out.warnings


async def test_dashboard_verified_legal_flag_downgrades(test_db, monkeypatch):
    """A verified legal flag at severity cao drops the verdict to cân nhắc."""
    _passthrough_narrator(monkeypatch)
    await _seed(test_db, "REQ-DASH-2", legal_flag=True)
    ctx = AIServiceContext(
        user_id="u1", service_id="property_dashboard", db_session_factory=_factory(test_db)
    )
    out = await PropertyDashboardService().run(PropertyDashboardInput(case_id="REQ-DASH-2"), ctx)
    assert out.verdict.decision == VerdictDecision.CAN_NHAC
    assert out.verdict.downgraded is True


async def test_dashboard_no_risk_warns(test_db, monkeypatch):
    """No Màn 4 risk → no verdict + a warning (KPI also None without risk)."""
    _passthrough_narrator(monkeypatch)
    await _seed(test_db, "REQ-DASH-3", with_risk=False)
    ctx = AIServiceContext(
        user_id="u1", service_id="property_dashboard", db_session_factory=_factory(test_db)
    )
    out = await PropertyDashboardService().run(PropertyDashboardInput(case_id="REQ-DASH-3"), ctx)
    assert out.verdict is None
    assert out.kpi is None
    assert any("Màn 4" in w for w in out.warnings)


async def test_registry_discovers_property_dashboard():
    """The plugin is auto-discovered as an async service."""
    registry = AIServiceRegistry()
    registry.discover_and_register()
    service = registry.get("property_dashboard")
    assert service is not None
    assert service.meta.is_async is True
