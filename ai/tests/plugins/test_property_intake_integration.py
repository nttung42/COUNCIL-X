"""Integration tests for property_intake through the real service entry point.

Exercises the full path the Celery worker uses — ``PropertyIntakeService.run`` ->
LangGraph pipeline (ingest -> extract -> verify -> merge -> validate -> assemble)
— over the 4 sample documents, with the LLM mocked per output schema. Asserts the
cross-document merge, confidence tiering, contract output shape, and per-node
progress reporting.
"""

from __future__ import annotations

from shb.ai.plugins.base import AIServiceContext
from shb.ai.plugins.property_intake.nodes import extract as extract_mod
from shb.ai.plugins.property_intake.nodes import ingest as ingest_mod
from shb.ai.plugins.property_intake.nodes import verify as verify_mod
from shb.ai.plugins.property_intake.schema import (
    DocType,
    FieldStatus,
    PropertyIntakeInput,
    PropertyIntakeOutput,
)
from shb.ai.plugins.property_intake.service import PropertyIntakeService
from tests.plugins._pi_fixtures import (
    SAMPLE_TEXTS,
    classify_by_token,
    extraction_router,
    storage_with_all_samples,
)


def _wire(monkeypatch):
    """Route classifier + extractor + verifier LLM calls to the offline fakes."""
    monkeypatch.setattr(extract_mod, "get_chat_model", lambda: extraction_router())
    monkeypatch.setattr(verify_mod, "get_chat_model", lambda: extraction_router())

    async def _classify(text, **_kwargs):
        return classify_by_token(text)

    monkeypatch.setattr(ingest_mod, "classify_document", _classify)


# --------------------------------------------------------------------------- #
# Fixtures sanity: every sample routes to its own DocType
# --------------------------------------------------------------------------- #
def test_sample_fixtures_classify_by_token():
    """Each of the 4 sample documents carries a token routing to its DocType."""
    for doc_type, text in SAMPLE_TEXTS.items():
        assert classify_by_token(text) == doc_type
    assert len(SAMPLE_TEXTS) == 4


# --------------------------------------------------------------------------- #
# Full service run over all 4 documents
# --------------------------------------------------------------------------- #
async def test_service_run_all_four_documents(monkeypatch):
    """End-to-end: 4 docs classified, extracted, reconciled into the form output."""
    _wire(monkeypatch)
    storage, file_ids = storage_with_all_samples()
    ctx = AIServiceContext(user_id="u1", service_id="property_intake", storage_service=storage)

    service = PropertyIntakeService()
    out = await service.run(PropertyIntakeInput(file_ids=file_ids, case_id="REQ-2026-0001"), ctx)

    # Output validates against the contract model.
    assert isinstance(out, PropertyIntakeOutput)
    assert out.case_id == "REQ-2026-0001"

    # All four documents were read and classified distinctly.
    assert len(out.documents) == 4
    detected = {d.detected_doc_type for d in out.documents}
    assert detected == {
        DocType.SO_DO_SO_HONG,
        DocType.TO_KHAI_LPTB,
        DocType.BIEN_BAN_BAN_GIAO,
        DocType.THONG_BAO_THUE_DAT,
    }

    by_key = {f.key: f for f in out.fields}

    # Owner corroborated across all 4 docs -> verified & auto-filled.
    owner = by_key["owner_full_name"]
    assert owner.value == "Nguyễn Văn A"
    assert owner.status == FieldStatus.DA_XAC_THUC
    assert owner.target_table == "case_borrower" and owner.target_field == "full_name"

    # land_area: GCN/tờ khai say 62, thông báo thuế says 80 -> conflict, GCN wins.
    area = by_key["land_area_sqm"]
    assert area.value == "62"
    assert area.normalized == 62.0
    assert area.status == FieldStatus.MAU_THUAN
    assert "80" in [alt.value for alt in area.alternatives]

    # Conflict surfaced as a case-level warning.
    assert any("mâu thuẫn" in w for w in out.warnings)

    # frontage×depth (4×15=60) ≈ diện tích (62) -> no validation flag.
    assert by_key["land_area_sqm"].validation_flags == []


async def test_service_run_reports_progress_to_completion(monkeypatch):
    """update_progress is invoked per node, monotonically, ending at 100."""
    _wire(monkeypatch)
    storage, file_ids = storage_with_all_samples()

    seen: list[int] = []
    ctx = AIServiceContext(
        user_id="u1",
        service_id="property_intake",
        storage_service=storage,
        update_progress=seen.append,
    )

    service = PropertyIntakeService()
    await service.run(PropertyIntakeInput(file_ids=file_ids), ctx)

    assert seen, "expected progress callbacks"
    assert seen == sorted(seen), "progress must be non-decreasing"
    assert seen[-1] == 100


async def test_service_run_partial_when_one_file_missing(monkeypatch):
    """A missing file id degrades gracefully: a warning, other docs still processed."""
    _wire(monkeypatch)
    storage, file_ids = storage_with_all_samples()
    ctx = AIServiceContext(user_id="u1", service_id="property_intake", storage_service=storage)

    service = PropertyIntakeService()
    out = await service.run(PropertyIntakeInput(file_ids=file_ids + ["ghost"]), ctx)

    assert len(out.documents) == 4  # ghost skipped
    assert any("ghost" in w for w in out.warnings)
