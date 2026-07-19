"""End-to-end harness F1 → F2 → F3 → F4 → F5 on ONE fresh case, product-style.

Runs the REAL services (real LLM + Postgres), persisting each stage's output the
way the backend would, then CROSS-CHECKS every downstream value against the
persisted ground truth and the deterministic engine math. Finally it hits the
LIVE public HTTP API (F5) on the same case and asserts the HTTP result equals the
in-process/DB values.

  1. F1 property_intake  : upload 4 real sample PDFs → extract Màn 1 → persist.
  2. Research (SIMULATED, out of scope): write Màn 2 findings/comparables/index.
  3. F2 property_lookup  : read Màn 2; assert counts/badges match what was written.
  4. F3 property_valuation: compute; persist valuation_result(+methods); assert math.
  5. F4 property_risk    : compute; persist risk_assessment_result(+groups/flags);
                           assert LTV == policy band for the score, label == band.
  6. F5 property_dashboard: aggregate; assert KPI == persisted F3/F4, verdict +
                           max_loan recomputed independently, narrator kept numbers.
  7. HTTP round-trip     : POST /services/property_dashboard/run (public) + poll;
                           assert HTTP KPI/verdict == in-process.

Run from ai/ on the host (uses .env: LLM_* + DATABASE_URL on :5433; Docker up):

    .venv/Scripts/python.exe scripts/e2e_f1_to_f5.py
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import re
import sys
import urllib.request
from pathlib import Path

from sqlalchemy import delete, func, select

from shb.ai.plugins.base import AIServiceContext
from shb.ai.plugins.property_dashboard.schema import PropertyDashboardInput
from shb.ai.plugins.property_dashboard.service import PropertyDashboardService
from shb.ai.plugins.property_intake.schema import PropertyIntakeInput
from shb.ai.plugins.property_intake.service import PropertyIntakeService
from shb.ai.plugins.property_lookup.schema import PropertyLookupInput
from shb.ai.plugins.property_lookup.service import PropertyLookupService
from shb.ai.plugins.property_risk.schema import PropertyRiskInput
from shb.ai.plugins.property_risk.service import PropertyRiskService
from shb.ai.plugins.property_valuation.schema import PropertyValuationInput
from shb.ai.plugins.property_valuation.service import PropertyValuationService
from shb.capabilities.dashboard.synthesis import (
    SynthesisInputs,
    VerdictFlag,
    compute_verdict,
)
from shb.core.db import AsyncSessionLocal
from shb.db.models import User
from shb.db.models_paa import (
    AppraisalCase,
    AttachedDocument,
    CaseBorrower,
    ExtractedDocType,
    ExtractionFieldStatus,
    FieldProvenance,
    LookupBadge,
    LookupCategory,
    LookupFinding,
    MarketComparable,
    PropertyLegalInfo,
    PropertyPhysicalInfo,
    RiskAssessmentResult,
    RiskFlag,
    RiskGroup,
    RiskLtvPolicyBand,
    SeverityLevel,
    ValuationMethod,
    ValuationPriceIndexPoint,
    ValuationResult,
    VerificationStatus,
)
from shb.services.storage_service import StorageService

CASE_ID = "REQ-E2E-0005"
API = "http://localhost:8888/api/v1"
SAMPLES = [
    "samples/01_So_hong_GCN_QSDD.pdf",
    "samples/02_To_khai_le_phi_truoc_ba.pdf",
    "samples/03_Bien_ban_ban_giao (1).pdf",
    "samples/04_Thong_bao_thue_dat (1).pdf",
]
_NUMERIC = {"land_area_sqm", "floor_area_sqm", "frontage_m", "depth_m", "alley_width_m"}
_INT = {"construction_year", "loan_term_years", "loan_amount_vnd"}

_PASS = 0
_FAIL = 0


def _rule(t: str) -> None:
    print(f"\n{'=' * 6} {t} {'=' * 6}")


def check(name: str, cond: bool, detail: str = "") -> bool:
    """Record and print one assertion."""
    global _PASS, _FAIL
    ok = bool(cond)
    _PASS += ok
    _FAIL += not ok
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f"  — {detail}" if detail else ""))
    return ok


def _digits(v) -> str:
    return re.sub(r"\D", "", str(v))


# --------------------------------------------------------------------------- #
# F1 persistence + Màn 2 simulation (same as e2e_f1_f2_f3, kept local)
# --------------------------------------------------------------------------- #
def _col_value(f):
    if f.target_field in _NUMERIC and isinstance(f.normalized, (int, float)):
        return float(f.normalized)
    if f.target_field in _INT and isinstance(f.normalized, int):
        return f.normalized
    if f.target_field == "issue_date":
        # DATE column: only a real date may pass — never the raw string.
        for cand in (f.normalized, f.value):
            if not isinstance(cand, str):
                continue
            try:
                return dt.date.fromisoformat(cand)
            except ValueError:
                pass
            m = re.search(
                r"(\d{1,2})\D+(\d{1,2})\D+(\d{4})", cand
            )  # 14/03/2019, 14 tháng 03 năm 2019
            if m:
                try:
                    return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                except ValueError:
                    pass
        return None
    return f.value


async def _persist_man1(session, output, file_map) -> list[str]:
    session.add(AppraisalCase(case_id=CASE_ID, requested_by="e2e-f1f5", current_step=1))
    for doc in output.documents:
        session.add(
            AttachedDocument(
                id=file_map[doc.file_id],
                case_id=CASE_ID,
                file_name=doc.file_name,
                file_type=doc.file_name.rsplit(".", 1)[-1].lower(),
                detected_doc_type=ExtractedDocType(doc.detected_doc_type.value),
                is_scan=doc.is_scan,
                page_count=doc.page_count,
            )
        )
    tables: dict[str, dict] = {}
    for f in output.fields:
        if f.value is None or f.status.value == "nhap_tay":
            continue
        tables.setdefault(f.target_table, {})[f.target_field] = _col_value(f)
    written = []
    tb = tables.get("case_borrower", {})
    if tb.get("full_name") and tb.get("national_id"):
        session.add(CaseBorrower(case_id=CASE_ID, **tb))
        written.append("case_borrower")
    tb = tables.get("property_legal_info", {})
    if tb.get("certificate_type") and tb.get("certificate_number"):
        session.add(PropertyLegalInfo(case_id=CASE_ID, **tb))
        written.append("property_legal_info")
    tb = tables.get("property_physical_info", {})
    if tb.get("address") and tb.get("property_type") and tb.get("land_area_sqm") is not None:
        session.add(PropertyPhysicalInfo(case_id=CASE_ID, **tb))
        written.append("property_physical_info")
    for f in output.fields:
        if f.value is None or f.status.value == "nhap_tay":
            continue
        session.add(
            FieldProvenance(
                case_id=CASE_ID,
                source_document_id=file_map.get(f.source_file_id),
                target_table=f.target_table,
                target_field=f.target_field,
                extracted_value=f.value,
                source_snippet=f.source_snippet,
                source_page=f.source_page,
                confidence_pct=f.confidence_pct,
                status=ExtractionFieldStatus(f.status.value),
                is_selected=True,
            )
        )
    await session.commit()
    return written


# Deterministic Màn 2 for the case (stand-in for the out-of-scope research pipeline).
_COMPS = [
    ("Hẻm 40 Nguyễn Văn A", 0.3, 58, "2025-11-10", 148_000_000),
    ("Đường Nguyễn Văn A", 0.6, 65, "2025-09-05", 152_000_000),
    ("Hẻm 12 Trần Văn B", 0.8, 60, "2025-06-20", 145_000_000),
    ("Hẻm 45 kế bên", 0.1, 64, "2026-02-15", 158_000_000),
    ("Đường Lê Văn C", 1.1, 70, "2026-01-08", 150_000_000),
]
_FINDINGS = [
    (LookupCategory.MARKET_PRICE, LookupBadge.DA_XAC_THUC, 80, "Giá thị trường"),
    (LookupCategory.PLANNING_ZONING, LookupBadge.DA_XAC_THUC, 90, "Quy hoạch"),
    (LookupCategory.LEGAL_STATUS, LookupBadge.DA_XAC_THUC, 92, "Pháp lý"),
    (LookupCategory.NEIGHBORHOOD_AMENITY, LookupBadge.DA_XAC_THUC, 82, "Tiện ích"),
    (LookupCategory.ENVIRONMENTAL_RISK, LookupBadge.LUU_Y, 60, "Môi trường"),
    (LookupCategory.LIQUIDITY_STAT, LookupBadge.DA_XAC_THUC, 85, "Thanh khoản"),
    (LookupCategory.STIGMA_REPUTATION, LookupBadge.DA_XAC_THUC, 95, "Dư luận"),
]
_INDEX = [
    ("2024-Q1", 100),
    ("2024-Q3", 106),
    ("2025-Q1", 111),
    ("2025-Q3", 115),
    ("2026-Q1", 118),
    ("2026-Q2", 120),
]


async def _simulate_research(session) -> None:
    for i, (addr, dist, area, d, ppm) in enumerate(_COMPS):
        session.add(
            MarketComparable(
                case_id=CASE_ID,
                comp_address=addr,
                distance_km=dist,
                area_sqm=area,
                transaction_date=dt.date.fromisoformat(d),
                price_per_sqm_vnd=ppm,
                display_order=i,
            )
        )
    for cat, badge, conf, title in _FINDINGS:
        session.add(
            LookupFinding(
                case_id=CASE_ID,
                category=cat,
                tool_name=f"{cat.value}_lookup",
                status_badge=badge,
                title=title,
                raw_findings=[f"Dữ liệu mô phỏng cho {title}"],
                inference_text=f"Nhận định mô phỏng: {title} ổn.",
                source_label=f"{cat.value}_lookup",
                confidence_pct=conf,
            )
        )
    for i, (period, idx) in enumerate(_INDEX):
        session.add(
            ValuationPriceIndexPoint(
                case_id=CASE_ID, period_label=period, index_value=idx, display_order=i
            )
        )
    await session.commit()


async def _persist_valuation(session, out3) -> None:
    v = out3.valuation
    session.add(
        ValuationResult(
            case_id=CASE_ID,
            proposed_value_vnd=v.proposed_value_vnd,
            value_range_low_vnd=v.value_range_low_vnd,
            value_range_high_vnd=v.value_range_high_vnd,
            price_per_sqm_vnd=v.price_per_sqm_vnd,
            confidence_pct=v.confidence_pct,
            comparable_count=v.comparable_count,
            price_index_period=v.price_index_period,
            price_index_value=v.price_index_value,
            confidence_inference_text=v.confidence_inference_text,
        )
    )
    for m in out3.methods:
        session.add(
            ValuationMethod(
                case_id=CASE_ID,
                method_key=m.method_key.value,
                estimated_value_vnd=m.estimated_value_vnd,
                weight_pct=m.weight_pct,
                contribution_value_vnd=m.contribution_value_vnd,
                method_confidence_pct=m.method_confidence_pct,
                inputs=m.inputs,
                inference_text=m.inference_text,
                source_label=m.source_label,
            )
        )
    await session.commit()


async def _persist_risk(session, out4) -> None:
    a = out4.assessment
    session.add(
        RiskAssessmentResult(
            case_id=CASE_ID,
            risk_score=a.risk_score,
            risk_label=SeverityLevel(a.risk_label.value),
            ltv_proposed_pct=a.ltv_proposed_pct,
            risk_inference_text=a.risk_inference_text,
        )
    )
    group_id_by_label: dict[str, str] = {}
    for g in out4.groups:
        rg = RiskGroup(
            case_id=CASE_ID,
            group_key=g.group_key.value,
            label=g.label,
            weight_pct=g.weight_pct,
            score=g.score,
            raw_findings=g.signals,
            source_label=g.group_key.value,
        )
        session.add(rg)
        await session.flush()
        group_id_by_label[g.label] = rg.id
    for i, fl in enumerate(out4.flags):
        session.add(
            RiskFlag(
                case_id=CASE_ID,
                severity=SeverityLevel(fl.severity.value),
                title=fl.title,
                description=fl.description,
                confidence_pct=fl.confidence_pct,
                verified_status=(
                    VerificationStatus.DA_XAC_THUC
                    if fl.verified
                    else VerificationStatus.CHUA_XAC_THUC
                ),
                linked_risk_group=group_id_by_label.get(fl.title),
                display_order=i,
            )
        )
    await session.commit()


def _http_json(method: str, url: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


async def main() -> None:
    """Run the full F1→F5 chain with per-stage persistence + cross-checks."""
    _rule("SETUP")
    for p in SAMPLES:
        if not Path(p).exists():
            print(f"  MISSING sample: {p}")
            sys.exit(2)
    async with AsyncSessionLocal() as s:
        user = (await s.execute(select(User).limit(1))).scalar_one_or_none()
        if user is None:
            print("  no user in DB; run the app once so a default user exists.")
            sys.exit(2)
        uid = user.id
        await s.execute(delete(AppraisalCase).where(AppraisalCase.case_id == CASE_ID))
        await s.commit()
    print(f"  case={CASE_ID}  user={uid}")

    # ---- F1 --------------------------------------------------------------- #
    _rule("F1 · property_intake (upload 4 PDF thật + extract, real LLM)")
    file_ids = []
    async with AsyncSessionLocal() as s:
        storage = StorageService(s)
        for path in SAMPLES:
            rec = await storage.save_upload(
                uid, Path(path).name, Path(path).read_bytes(), "application/pdf"
            )
            file_ids.append(rec.id)
        await storage.commit()
    async with AsyncSessionLocal() as s:
        ctx = AIServiceContext(
            user_id=uid, service_id="property_intake", storage_service=StorageService(s)
        )
        out1 = await PropertyIntakeService().run(
            PropertyIntakeInput(file_ids=file_ids, case_id=CASE_ID), ctx
        )
    filled = [f for f in out1.fields if f.value is not None]
    check("F1 trích xuất được field", len(filled) > 0, f"{len(filled)}/{len(out1.fields)} field")
    check("F1 nhận đủ 4 tài liệu", len(out1.documents) == 4, f"{len(out1.documents)} docs")

    file_map = {fid: f"adoc-{i}-{CASE_ID}" for i, fid in enumerate(file_ids)}
    async with AsyncSessionLocal() as s:
        written = await _persist_man1(s, out1, file_map)
    check("F1 persist property_physical_info", "property_physical_info" in written, str(written))
    async with AsyncSessionLocal() as s:
        phys = await s.get(PropertyPhysicalInfo, CASE_ID)
        await s.get(PropertyLegalInfo, CASE_ID)  # warm check only
    check(
        "Màn 1 có địa chỉ + diện tích",
        phys and phys.address and phys.land_area_sqm,
        f"{getattr(phys, 'address', None)} · {getattr(phys, 'land_area_sqm', None)} m²",
    )

    # ---- Research (simulated) --------------------------------------------- #
    _rule("RESEARCH (mô phỏng — ngoài phạm vi) · ghi Màn 2")
    async with AsyncSessionLocal() as s:
        await _simulate_research(s)
    async with AsyncSessionLocal() as s:
        nc = await s.scalar(
            select(func.count())
            .select_from(MarketComparable)
            .where(MarketComparable.case_id == CASE_ID)
        )
        nf = await s.scalar(
            select(func.count()).select_from(LookupFinding).where(LookupFinding.case_id == CASE_ID)
        )
    check("Ghi đủ 5 comparable", nc == len(_COMPS), f"{nc}")
    check("Ghi đủ 7 finding", nf == len(_FINDINGS), f"{nf}")

    ctx_db = AIServiceContext(user_id=uid, service_id="x", db_session_factory=AsyncSessionLocal)

    # ---- F2 --------------------------------------------------------------- #
    _rule("F2 · property_lookup (đọc Màn 2 — đối chiếu)")
    out2 = await PropertyLookupService().run(PropertyLookupInput(case_id=CASE_ID), ctx_db)
    check("F2 đọc đúng số finding", len(out2.findings) == len(_FINDINGS), f"{len(out2.findings)}")
    check(
        "F2 đọc đúng số comparable",
        len(out2.market_comparables) == len(_COMPS),
        f"{len(out2.market_comparables)}",
    )
    env = next((f for f in out2.findings if f.category.value == "environmental_risk"), None)
    check(
        "F2 giữ đúng badge 'luu_y' của Môi trường",
        env and env.status_badge.value == "luu_y",
        getattr(getattr(env, "status_badge", None), "value", None),
    )

    # ---- F3 --------------------------------------------------------------- #
    _rule("F3 · property_valuation (tính Màn 1+2 → persist → đối chiếu)")
    out3 = await PropertyValuationService().run(PropertyValuationInput(case_id=CASE_ID), ctx_db)
    v = out3.valuation
    print(
        f"    proposed={v.proposed_value_vnd:,} range={v.value_range_low_vnd:,}..{v.value_range_high_vnd:,} conf={v.confidence_pct}%"
    )
    check(
        "F3 weights = 100",
        sum(m.weight_pct for m in out3.methods) == 100,
        str([m.weight_pct for m in out3.methods]),
    )
    check(
        "F3 proposed nằm trong range",
        v.value_range_low_vnd <= v.proposed_value_vnd <= v.value_range_high_vnd,
    )
    check("F3 confidence 0..100", 0 <= v.confidence_pct <= 100, f"{v.confidence_pct}")
    check("F3 comparable_count = 5", v.comparable_count == len(_COMPS), f"{v.comparable_count}")
    check(
        "F3 subjective bounded ±5%",
        abs(out3.subjective_adjustment.value_pct) <= 5.0,
        f"{out3.subjective_adjustment.value_pct:+}%",
    )
    async with AsyncSessionLocal() as s:
        await _persist_valuation(s, out3)
        vr = await s.get(ValuationResult, CASE_ID)
    check(
        "F3 persist == output (proposed_value)",
        vr.proposed_value_vnd == v.proposed_value_vnd,
        f"db={vr.proposed_value_vnd:,}",
    )

    # ---- F4 --------------------------------------------------------------- #
    _rule("F4 · property_risk (tính → persist → đối chiếu khung LTV)")
    out4 = await PropertyRiskService().run(PropertyRiskInput(case_id=CASE_ID), ctx_db)
    a = out4.assessment
    print(f"    risk_score={a.risk_score} label={a.risk_label.value} LTV={a.ltv_proposed_pct}%")
    check("F4 risk_score 0..100", 0 <= a.risk_score <= 100, f"{a.risk_score}")
    check("F4 nhóm weights = 100", sum(g.weight_pct for g in out4.groups) == 100)
    async with AsyncSessionLocal() as s:
        bands = list(
            (await s.execute(select(RiskLtvPolicyBand).order_by(RiskLtvPolicyBand.id))).scalars()
        )
    band = next(
        (
            b
            for b in bands
            if b.min_score <= a.risk_score and (b.max_score is None or a.risk_score <= b.max_score)
        ),
        None,
    )
    check(
        "F4 LTV khớp khung chính sách theo điểm",
        band and a.ltv_proposed_pct == band.max_ltv_pct,
        f"score {a.risk_score} → band {getattr(band, 'min_score', None)}-{getattr(band, 'max_score', None)} = {getattr(band, 'max_ltv_pct', None)}%",
    )
    _labels = {"thap": (0, 20), "trung_binh": (21, 40), "cao": (41, 60), "nghiem_trong": (61, 100)}
    lo, hi = _labels[a.risk_label.value]
    check("F4 label khớp điểm", lo <= a.risk_score <= hi, f"{a.risk_label.value} vs {a.risk_score}")
    async with AsyncSessionLocal() as s:
        await _persist_risk(s, out4)
        rr = await s.get(RiskAssessmentResult, CASE_ID)
    check(
        "F4 persist == output (risk_score, LTV)",
        rr.risk_score == a.risk_score and rr.ltv_proposed_pct == a.ltv_proposed_pct,
        f"db score={rr.risk_score} ltv={rr.ltv_proposed_pct}",
    )

    # ---- F5 --------------------------------------------------------------- #
    _rule("F5 · property_dashboard (tổng hợp → đối chiếu chéo F3/F4 + verdict)")
    out5 = await PropertyDashboardService().run(PropertyDashboardInput(case_id=CASE_ID), ctx_db)
    k = out5.kpi
    ver = out5.verdict
    print(
        f"    KPI value={k.proposed_value_vnd:,} risk={k.risk_score} {k.risk_label} LTV={k.ltv_proposed_pct}"
    )
    print(f"    VERDICT={ver.decision} max_loan={ver.max_loan_vnd:,} downgraded={ver.downgraded}")
    check("F5 KPI.proposed_value == F3 persisted", k.proposed_value_vnd == vr.proposed_value_vnd)
    check("F5 KPI.risk_score == F4 persisted", k.risk_score == rr.risk_score)
    check("F5 KPI.ltv == F4 persisted", k.ltv_proposed_pct == rr.ltv_proposed_pct)
    # independent recompute of the verdict from persisted ground truth
    vflags = [
        VerdictFlag(
            group_key="legal" if "Pháp lý" in fo.title else "other",
            severity=fo.severity.value,
            verified=fo.verified,
            title=fo.title,
        )
        for fo in out4.flags
    ]
    expected = compute_verdict(
        SynthesisInputs(
            risk_label=rr.risk_label.value,
            proposed_value_vnd=vr.proposed_value_vnd,
            ltv_proposed_pct=rr.ltv_proposed_pct,
            flags=vflags,
        )
    )
    check(
        "F5 verdict.decision == recompute độc lập",
        ver.decision == expected.decision,
        f"{ver.decision} vs {expected.decision}",
    )
    check(
        "F5 max_loan == round(value×LTV/100)",
        ver.max_loan_vnd == round(vr.proposed_value_vnd * rr.ltv_proposed_pct / 100),
        f"{ver.max_loan_vnd:,}",
    )
    check("F5 đủ 4 tóm tắt", len(out5.step_summaries) == 4)
    # narrator must preserve numbers (digit-substring, robust to comma/space reformat)
    joined = _digits(" ".join(s.summary_text for s in out5.step_summaries))
    gen = out5.step_summaries[0].generated_by
    check(
        f"F5 narrator giữ nguyên giá trị định giá (by {gen})",
        _digits(vr.proposed_value_vnd) in joined,
        "digits preserved",
    )
    check(
        "F5 narrator giữ nguyên LTV%",
        _digits(rr.ltv_proposed_pct) in joined,
        f"LTV {rr.ltv_proposed_pct}% xuất hiện trong tóm tắt",
    )
    check("F5 có trace + case_history", len(out5.case_history) > 0)

    # ---- HTTP round-trip -------------------------------------------------- #
    _rule("HTTP round-trip · F5 qua API public + poll (đối chiếu HTTP == in-process)")
    try:
        run = _http_json(
            "POST", f"{API}/services/property_dashboard/run", {"input": {"case_id": CASE_ID}}
        )
        job = run.get("job_id")
        result = None
        for _ in range(40):
            j = _http_json("GET", f"{API}/jobs/{job}")
            if j.get("status") in ("completed", "failed"):
                result = j.get("result")
                break
            await asyncio.sleep(1)
        hk = (result or {}).get("kpi") or {}
        hv = (result or {}).get("verdict") or {}
        check(
            "HTTP F5 KPI.proposed_value == in-process",
            hk.get("proposed_value_vnd") == k.proposed_value_vnd,
            f"{hk.get('proposed_value_vnd')}",
        )
        check(
            "HTTP F5 verdict.decision == in-process",
            hv.get("decision") == ver.decision,
            f"{hv.get('decision')}",
        )
        check("HTTP F5 max_loan == in-process", hv.get("max_loan_vnd") == ver.max_loan_vnd)
    except Exception as exc:  # noqa: BLE001
        check("HTTP round-trip reachable", False, str(exc))

    # ---- summary ---------------------------------------------------------- #
    _rule("KẾT QUẢ")
    print(f"  PASS={_PASS}  FAIL={_FAIL}")
    print("  Chuỗi F1→F2→F3→F4→F5 hoàn chỉnh, persist từng tầng + đối chiếu chéo + HTTP.")
    sys.exit(1 if _FAIL else 0)


if __name__ == "__main__":
    asyncio.run(main())
