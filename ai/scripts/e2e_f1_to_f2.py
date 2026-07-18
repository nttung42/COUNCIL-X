"""End-to-end harness: Function 1 (property_intake) -> DB -> Function 2 (property_lookup).

Runs the REAL services (real LLM, real Postgres) against a fresh case:

  1. Upload the 4 sample PDFs (ai/samples/) via StorageService.
  2. Run property_intake -> Màn 1 extraction JSON.
  3. Persist that Màn 1 output into the DB (appraisal_case + case_borrower +
     property_legal_info + property_physical_info + loan_info + attached_document
     + field_provenance) — the "backend PR5" glue, prototyped here to close the loop.
  4. Poke the DB (ORM reads) to prove Màn 1 + provenance landed correctly.
  5. Run property_lookup on the new case (no research data yet -> warning) and on a
     seeded case (REQ-2026-2000, fully populated) to show both branches.

Run from the ai/ directory on the host (connects to the Docker Postgres via .env
DATABASE_URL = localhost:5433):

    .venv/Scripts/python.exe scripts/e2e_f1_to_f2.py
"""

from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
from pathlib import Path

from sqlalchemy import delete, select

from shb.ai.plugins.base import AIServiceContext
from shb.ai.plugins.property_intake.schema import PropertyIntakeInput
from shb.ai.plugins.property_intake.service import PropertyIntakeService
from shb.ai.plugins.property_lookup.schema import PropertyLookupInput
from shb.ai.plugins.property_lookup.service import PropertyLookupService
from shb.core.db import AsyncSessionLocal
from shb.db.models import User
from shb.db.models_paa import (
    AppraisalCase,
    AttachedDocument,
    CaseBorrower,
    ExtractedDocType,
    ExtractionFieldStatus,
    FieldProvenance,
    LoanInfo,
    PropertyLegalInfo,
    PropertyPhysicalInfo,
)
from shb.services.storage_service import StorageService

CASE_ID = "REQ-E2E-0001"
SAMPLES = [
    "samples/01_so_hong.pdf",
    "samples/02_to_khai_lptb.pdf",
    "samples/03_bien_ban_ban_giao.pdf",
    "samples/04_thong_bao_thue_dat.pdf",
]

# Which target_field values are numeric/date columns → use FormField.normalized.
_NUMERIC = {
    "land_area_sqm",
    "floor_area_sqm",
    "frontage_m",
    "depth_m",
    "alley_width_m",
}
_INT = {"construction_year", "loan_term_years", "loan_amount_vnd"}


def _rule(title: str) -> None:
    print(f"\n{'=' * 4} {title} {'=' * 4}")


async def _ensure_user(session) -> str:
    user = (await session.execute(select(User).limit(1))).scalar_one_or_none()
    if user is None:
        user = User(email="e2e@shb.local", api_key_hash=hashlib.sha256(b"e2e").hexdigest())
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user.id


async def _reset_case(session) -> None:
    """Delete any prior E2E case so the harness is idempotent."""
    await session.execute(delete(AppraisalCase).where(AppraisalCase.case_id == CASE_ID))
    await session.commit()


def _col_value(field):
    """Pick the DB-ready value for a FormField: typed normalized, else verbatim."""
    if field.target_field in _NUMERIC and isinstance(field.normalized, (int, float)):
        return float(field.normalized)
    if field.target_field in _INT and isinstance(field.normalized, int):
        return field.normalized
    if field.target_field == "issue_date" and isinstance(field.normalized, str):
        try:
            return dt.date.fromisoformat(field.normalized)
        except ValueError:
            return None
    return field.value


async def _persist_man1(session, output, file_id_to_doc: dict[str, str]) -> dict:
    """Write the Màn 1 extraction into the DB; return a summary of what was written."""
    session.add(AppraisalCase(case_id=CASE_ID, requested_by="e2e-harness", current_step=1))

    # attached_document — one row per parsed doc; map storage file_id -> its id.
    for doc in output.documents:
        adoc = AttachedDocument(
            id=file_id_to_doc[doc.file_id],
            case_id=CASE_ID,
            file_name=doc.file_name,
            file_type=doc.file_name.rsplit(".", 1)[-1].lower(),
            detected_doc_type=ExtractedDocType(doc.detected_doc_type.value),
            is_scan=doc.is_scan,
            page_count=doc.page_count,
        )
        session.add(adoc)

    # Group selected field values by target table.
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
    tb = tables.get("loan_info", {})
    if tb.get("loan_amount_vnd") is not None:
        session.add(LoanInfo(case_id=CASE_ID, **tb))
        written.append("loan_info")

    # field_provenance — one row per selected value (+ each mau_thuan alternative).
    prov = 0
    for f in output.fields:
        if f.value is None or f.status.value == "nhap_tay":
            continue
        session.add(
            FieldProvenance(
                case_id=CASE_ID,
                source_document_id=file_id_to_doc.get(f.source_file_id),
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
        prov += 1
        for alt in f.alternatives:
            session.add(
                FieldProvenance(
                    case_id=CASE_ID,
                    source_document_id=file_id_to_doc.get(alt.source_file_id),
                    target_table=f.target_table,
                    target_field=f.target_field,
                    extracted_value=alt.value,
                    source_snippet=alt.source_snippet,
                    source_page=alt.source_page,
                    confidence_pct=alt.confidence_pct,
                    status=ExtractionFieldStatus.MAU_THUAN,
                    is_selected=False,
                )
            )
            prov += 1

    await session.commit()
    return {"tables": written, "provenance_rows": prov}


async def main() -> None:
    _rule("SETUP")
    async with AsyncSessionLocal() as s:
        uid = await _ensure_user(s)
        await _reset_case(s)
    print(f"user_id={uid}  case_id={CASE_ID}")

    # --- F1 step 1: upload the 4 sample PDFs ------------------------------------
    _rule("F1 · UPLOAD 4 sample PDFs")
    file_ids: list[str] = []
    async with AsyncSessionLocal() as s:
        storage = StorageService(s)
        for path in SAMPLES:
            data = Path(path).read_bytes()
            rec = await storage.save_upload(uid, Path(path).name, data, "application/pdf")
            file_ids.append(rec.id)
            print(f"  uploaded {Path(path).name} -> {rec.id}")
        await storage.commit()

    # --- F1 step 2: run property_intake ----------------------------------------
    _rule("F1 · RUN property_intake (real LLM)")
    async with AsyncSessionLocal() as s:
        ctx = AIServiceContext(
            user_id=uid, service_id="property_intake", storage_service=StorageService(s)
        )
        out1 = await PropertyIntakeService().run(
            PropertyIntakeInput(file_ids=file_ids, case_id=CASE_ID), ctx
        )
    filled = [f for f in out1.fields if f.value is not None]
    print(f"  documents={len(out1.documents)}  fields_filled={len(filled)}/{len(out1.fields)}")
    for f in filled[:8]:
        print(f"    [{f.status.value:11}] {f.label} = {f.value!r} ({f.confidence_pct}%)")

    # --- F1 step 3: persist Màn 1 into the DB ----------------------------------
    _rule("F1 · PERSIST Màn 1 -> DB")
    file_id_to_doc = {fid: f"adoc-{i}-{CASE_ID}" for i, fid in enumerate(file_ids)}
    async with AsyncSessionLocal() as s:
        summary = await _persist_man1(s, out1, file_id_to_doc)
    print(f"  wrote tables: {summary['tables']}")
    print(f"  field_provenance rows: {summary['provenance_rows']}")

    # --- Poke the DB: prove Màn 1 landed ---------------------------------------
    _rule("POKE DB · Màn 1 rows for the case")
    async with AsyncSessionLocal() as s:
        phys = (
            await s.execute(
                select(PropertyPhysicalInfo).where(PropertyPhysicalInfo.case_id == CASE_ID)
            )
        ).scalar_one_or_none()
        borrower = (
            await s.execute(select(CaseBorrower).where(CaseBorrower.case_id == CASE_ID))
        ).scalar_one_or_none()
        prov_rows = (
            await s.execute(select(FieldProvenance).where(FieldProvenance.case_id == CASE_ID))
        ).scalars().all()
        adocs = (
            await s.execute(select(AttachedDocument).where(AttachedDocument.case_id == CASE_ID))
        ).scalars().all()
    print(f"  attached_document: {len(adocs)} rows")
    if borrower:
        print(f"  case_borrower: {borrower.full_name} · {borrower.national_id}")
    if phys:
        print(
            f"  property_physical_info: {phys.address} · {phys.property_type} · "
            f"{phys.land_area_sqm} m²"
        )
    print(f"  field_provenance: {len(prov_rows)} rows (is_selected + alternatives)")
    sample_prov = next((p for p in prov_rows if p.target_field == "land_area_sqm"), None)
    if sample_prov:
        print(
            f"    e.g. land_area_sqm='{sample_prov.extracted_value}' "
            f"conf={sample_prov.confidence_pct}% status={sample_prov.status.value} "
            f"src_doc={sample_prov.source_document_id}"
        )

    # --- F2 on the NEW case: honest 'no research data yet' ----------------------
    _rule("F2 · property_lookup on the NEW case (no Màn 2 data yet)")
    ctx2 = AIServiceContext(
        user_id=uid, service_id="property_lookup", db_session_factory=AsyncSessionLocal
    )
    out2 = await PropertyLookupService().run(PropertyLookupInput(case_id=CASE_ID), ctx2)
    print(f"  findings={len(out2.findings)}  badges={_badge_counts(out2)}")
    print(f"  warnings={out2.warnings}")

    # --- F2 on a SEEDED case: fully populated ----------------------------------
    _rule("F2 · property_lookup on a SEEDED case (REQ-2026-2000)")
    out3 = await PropertyLookupService().run(PropertyLookupInput(case_id="REQ-2026-2000"), ctx2)
    print(f"  findings={len(out3.findings)}  comparables={len(out3.market_comparables)}")
    for f in out3.findings:
        print(f"    {f.category.value:22} {f.status_badge.value:12} {f.confidence_pct}%")

    print("\nDONE — F1 wrote Màn 1 to DB, F2 read the DB. Full loop exercised.")


def _badge_counts(out) -> dict:
    counts: dict = {}
    for f in out.findings:
        counts[f.status_badge.value] = counts.get(f.status_badge.value, 0) + 1
    return counts


if __name__ == "__main__":
    asyncio.run(main())
