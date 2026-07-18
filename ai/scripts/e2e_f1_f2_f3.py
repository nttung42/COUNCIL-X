"""End-to-end harness: F1 (intake) → [research sim] → F2 (lookup) → F3 (valuation).

Runs the REAL services (real LLM + Postgres) on a single fresh case, poking the DB
at each stage:

  1. F1 property_intake: upload 4 sample PDFs → extract Màn 1 → persist to DB.
  2. Research (SIMULATED — the real research pipeline is out of scope): write
     Màn 2 market_comparable + lookup_finding + a price-index series for the case,
     so F2/F3 have their inputs. Clearly labelled; swap for the real pipeline later.
  3. F2 property_lookup: read the 7 findings + comparables from DB.
  4. F3 property_valuation: compute the valuation from Màn 1 + Màn 2.

Run from ai/ on the host (needs LLM_* exported + Docker Postgres on :5433):

    export LLM_API_KEY=... LLM_BASE_URL=... LLM_MODEL=...
    .venv/Scripts/python.exe scripts/e2e_f1_f2_f3.py
"""

from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
from pathlib import Path

from sqlalchemy import delete, func, select

from shb.ai.plugins.base import AIServiceContext
from shb.ai.plugins.property_intake.schema import PropertyIntakeInput
from shb.ai.plugins.property_intake.service import PropertyIntakeService
from shb.ai.plugins.property_lookup.schema import PropertyLookupInput
from shb.ai.plugins.property_lookup.service import PropertyLookupService
from shb.ai.plugins.property_valuation.schema import PropertyValuationInput
from shb.ai.plugins.property_valuation.service import PropertyValuationService
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
    ValuationPriceIndexPoint,
)
from shb.services.storage_service import StorageService

CASE_ID = "REQ-E2E-0002"
SAMPLES = [
    "samples/01_so_hong.pdf",
    "samples/02_to_khai_lptb.pdf",
    "samples/03_bien_ban_ban_giao.pdf",
    "samples/04_thong_bao_thue_dat.pdf",
]
_NUMERIC = {"land_area_sqm", "floor_area_sqm", "frontage_m", "depth_m", "alley_width_m"}
_INT = {"construction_year", "loan_term_years", "loan_amount_vnd"}


def _rule(t: str) -> None:
    print(f"\n{'=' * 4} {t} {'=' * 4}")


def _col_value(f):
    if f.target_field in _NUMERIC and isinstance(f.normalized, (int, float)):
        return float(f.normalized)
    if f.target_field in _INT and isinstance(f.normalized, int):
        return f.normalized
    if f.target_field == "issue_date" and isinstance(f.normalized, str):
        try:
            return dt.date.fromisoformat(f.normalized)
        except ValueError:
            return None
    return f.value


async def _persist_man1(session, output, file_map) -> list[str]:
    session.add(AppraisalCase(case_id=CASE_ID, requested_by="e2e-f1f2f3", current_step=1))
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


async def _simulate_research(session) -> None:
    """Stand-in for the (out-of-scope) research pipeline: write Màn 2 for the case."""
    comps = [
        ("Hẻm 40 Nguyễn Văn A", 0.3, 58, "2025-11-10", 148_000_000),
        ("Đường Nguyễn Văn A", 0.6, 65, "2025-09-05", 152_000_000),
        ("Hẻm 12 Trần Văn B", 0.8, 60, "2025-06-20", 145_000_000),
        ("Hẻm 45 kế bên", 0.1, 64, "2026-02-15", 158_000_000),
        ("Đường Lê Văn C", 1.1, 70, "2026-01-08", 150_000_000),
    ]
    for i, (addr, dist, area, d, ppm) in enumerate(comps):
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
    findings = [
        (LookupCategory.MARKET_PRICE, LookupBadge.DA_XAC_THUC, 80, "Giá thị trường"),
        (LookupCategory.PLANNING_ZONING, LookupBadge.DA_XAC_THUC, 90, "Quy hoạch"),
        (LookupCategory.LEGAL_STATUS, LookupBadge.DA_XAC_THUC, 92, "Pháp lý"),
        (LookupCategory.NEIGHBORHOOD_AMENITY, LookupBadge.DA_XAC_THUC, 82, "Tiện ích"),
        (LookupCategory.ENVIRONMENTAL_RISK, LookupBadge.LUU_Y, 60, "Môi trường"),
        (LookupCategory.LIQUIDITY_STAT, LookupBadge.DA_XAC_THUC, 85, "Thanh khoản"),
        (LookupCategory.STIGMA_REPUTATION, LookupBadge.DA_XAC_THUC, 95, "Dư luận"),
    ]
    for cat, badge, conf, title in findings:
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
    for i, (period, idx) in enumerate(
        [("2024-Q1", 100), ("2024-Q3", 106), ("2025-Q1", 111), ("2025-Q3", 115), ("2026-Q1", 118), ("2026-Q2", 120)]
    ):
        session.add(
            ValuationPriceIndexPoint(
                case_id=CASE_ID, period_label=period, index_value=idx, display_order=i
            )
        )
    await session.commit()


async def main() -> None:
    _rule("SETUP")
    async with AsyncSessionLocal() as s:
        user = (await s.execute(select(User).limit(1))).scalar_one_or_none()
        if user is None:
            user = User(email="e2e3@shb.local", api_key_hash=hashlib.sha256(b"e2e3").hexdigest())
            s.add(user)
            await s.commit()
            await s.refresh(user)
        uid = user.id
        await s.execute(delete(AppraisalCase).where(AppraisalCase.case_id == CASE_ID))
        await s.commit()
    print(f"case={CASE_ID}")

    # ---- F1 ---------------------------------------------------------------
    _rule("F1 · property_intake (upload + extract, real LLM)")
    file_ids = []
    async with AsyncSessionLocal() as s:
        storage = StorageService(s)
        for path in SAMPLES:
            rec = await storage.save_upload(uid, Path(path).name, Path(path).read_bytes(), "application/pdf")
            file_ids.append(rec.id)
        await storage.commit()
    async with AsyncSessionLocal() as s:
        ctx = AIServiceContext(user_id=uid, service_id="property_intake", storage_service=StorageService(s))
        out1 = await PropertyIntakeService().run(PropertyIntakeInput(file_ids=file_ids, case_id=CASE_ID), ctx)
    filled = [f for f in out1.fields if f.value is not None]
    print(f"  extracted {len(filled)}/{len(out1.fields)} fields")

    file_map = {fid: f"adoc-{i}-{CASE_ID}" for i, fid in enumerate(file_ids)}
    async with AsyncSessionLocal() as s:
        written = await _persist_man1(s, out1, file_map)
    print(f"  persisted Màn 1 tables: {written}")

    # ---- Research (simulated) --------------------------------------------
    _rule("RESEARCH (SIMULATED) · ghi Màn 2 cho case")
    async with AsyncSessionLocal() as s:
        await _simulate_research(s)
    async with AsyncSessionLocal() as s:
        nc = await s.scalar(select(func.count()).select_from(MarketComparable).where(MarketComparable.case_id == CASE_ID))
        nf = await s.scalar(select(func.count()).select_from(LookupFinding).where(LookupFinding.case_id == CASE_ID))
        phys = await s.get(PropertyPhysicalInfo, CASE_ID)
    print(f"  wrote {nc} comparables, {nf} findings")
    print(f"  POKE DB · property_physical_info: {phys.address} · {phys.land_area_sqm} m² · {phys.property_type}")

    ctx_db = AIServiceContext(user_id=uid, service_id="x", db_session_factory=AsyncSessionLocal)

    # ---- F2 ---------------------------------------------------------------
    _rule("F2 · property_lookup (đọc Màn 2)")
    out2 = await PropertyLookupService().run(PropertyLookupInput(case_id=CASE_ID), ctx_db)
    print(f"  findings={len(out2.findings)} comparables={len(out2.market_comparables)} warnings={len(out2.warnings)}")

    # ---- F3 ---------------------------------------------------------------
    _rule("F3 · property_valuation (tính từ Màn 1 + Màn 2)")
    out3 = await PropertyValuationService().run(PropertyValuationInput(case_id=CASE_ID), ctx_db)
    v = out3.valuation
    print(f"  proposed: {v.proposed_value_vnd:,} ({v.value_range_low_vnd:,}..{v.value_range_high_vnd:,})")
    print(f"  price/m²: {v.price_per_sqm_vnd:,} | confidence {v.confidence_pct}% | comps {v.comparable_count}")
    for m in out3.methods:
        print(f"    {m.method_key:18} {m.estimated_value_vnd:>16,}  w={m.weight_pct}%")
    sa = out3.subjective_adjustment
    print(f"  SUBJECTIVE (LLM): {sa.value_pct:+}% · {sa.source} · {sa.reason[:60]}")
    assert sum(m.weight_pct for m in out3.methods) == 100
    print("\nDONE — F1 (ghi Màn 1) → research (Màn 2) → F2 (đọc) → F3 (định giá). Chuỗi hoàn chỉnh.")


if __name__ == "__main__":
    asyncio.run(main())
