"""Extract node: pull structured fields from each classified document.

PR3 supports four document types, each with its own extraction schema + prompt:
Sổ đỏ/hồng (GCN), Tờ khai lệ phí trước bạ, Biên bản bàn giao, Thông báo thuế đất.
All run over text-based PDFs/DOCX; scanned pages defer to vision OCR (later PR).

Group-A guarantees applied here:

* **Mandatory grounding** — a value whose text is not found in its source
  ``snippet`` is dropped (treated as null), never surfaced with low confidence.
* **Null-instead-of-guess** — enforced in the prompts; missing fields stay absent.
* **Verbatim + code normalizer** — ``value`` is kept verbatim; ``normalized``
  holds the typed value from :mod:`documents` (money → int, area → float,
  date → ISO).
"""

from __future__ import annotations

import logging
from typing import Callable

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from shb.ai.llm import get_chat_model
from shb.ai.plugins.property_intake.documents import CONF_HIGH, normalize_field
from shb.ai.plugins.property_intake.prompts import (
    BIEN_BAN_BAN_GIAO_SYSTEM,
    SO_HONG_SYSTEM,
    THONG_BAO_THUE_DAT_SYSTEM,
    TO_KHAI_LPTB_SYSTEM,
)
from shb.ai.plugins.property_intake.schema import (
    BienBanBanGiaoExtraction,
    DocType,
    ExtractedField,
    FieldStatus,
    FieldValue,
    SoHongExtraction,
    ThongBaoThueDatExtraction,
    ToKhaiLPTBExtraction,
)
from shb.ai.plugins.property_intake.state import IngestedDoc, IntakeState

logger = logging.getLogger(__name__)


# Per-document-type extraction schema + system prompt. Field names on each schema
# match canonical keys, so a single generic mapper turns any extraction into
# canonical values.
_EXTRACTORS: dict[DocType, tuple[type[BaseModel], str]] = {
    DocType.SO_DO_SO_HONG: (SoHongExtraction, SO_HONG_SYSTEM),
    DocType.TO_KHAI_LPTB: (ToKhaiLPTBExtraction, TO_KHAI_LPTB_SYSTEM),
    DocType.BIEN_BAN_BAN_GIAO: (BienBanBanGiaoExtraction, BIEN_BAN_BAN_GIAO_SYSTEM),
    DocType.THONG_BAO_THUE_DAT: (ThongBaoThueDatExtraction, THONG_BAO_THUE_DAT_SYSTEM),
}


def _build_extractor(schema: type[BaseModel]):
    """Return an LLM runnable that yields a validated instance of ``schema``."""
    return get_chat_model().with_structured_output(schema)


def _is_grounded(value: str, snippet: str | None) -> bool:
    """Return True when a value's (normalized) text appears in its snippet."""
    if not snippet:
        return False
    norm = " ".join(value.lower().split())
    hay = " ".join(snippet.lower().split())
    return norm in hay


def _snippet_page(doc: IngestedDoc, snippet: str | None) -> int | None:
    """Return the 1-indexed page whose text contains ``snippet`` (best effort)."""
    pages = doc.parsed.pages
    if not pages:
        return None
    if len(pages) == 1:
        return pages[0].page_number
    if not snippet:
        return None
    needle = " ".join(snippet.lower().split())
    for page in pages:
        if needle and needle in " ".join(page.text.lower().split()):
            return page.page_number
    return None


def _to_field_value(key: str, ef: ExtractedField | None, doc: IngestedDoc) -> FieldValue | None:
    """Map a raw extracted field to a canonical :class:`FieldValue`, or None.

    Enforces mandatory grounding: an ungrounded value is dropped (returns None).
    """
    if ef is None or not ef.value or not str(ef.value).strip():
        return None

    raw = str(ef.value).strip()

    # Group-A: mandatory grounding — no traceable source span => treat as null.
    if not _is_grounded(raw, ef.snippet):
        logger.debug("Dropping ungrounded field '%s' from %s", key, doc.file_name)
        return None

    confidence = float(ef.confidence or 0.0)
    status = FieldStatus.DA_XAC_THUC if confidence >= CONF_HIGH else FieldStatus.CAN_XAC_MINH
    return FieldValue(
        value=raw,
        normalized=normalize_field(key, raw),
        confidence=round(confidence, 2),
        status=status,
        source_doc=doc.file_name,
        source_file_id=doc.file_id,
        source_doc_type=doc.doc_type,
        source_page=_snippet_page(doc, ef.snippet),
        source_snippet=ef.snippet,
    )


def _map_extraction(extraction: BaseModel, doc: IngestedDoc) -> dict[str, FieldValue]:
    """Map any extraction whose field names are canonical keys into FieldValues."""
    canonical: dict[str, FieldValue] = {}
    for key in type(extraction).model_fields:
        fv = _to_field_value(key, getattr(extraction, key, None), doc)
        if fv is not None:
            canonical[key] = fv
    return canonical


def _map_so_hong(extraction: BaseModel, doc: IngestedDoc) -> dict[str, FieldValue]:
    """Map a Sổ hồng extraction, deriving the owner-asset relationship."""
    canonical = _map_extraction(extraction, doc)
    # Derive relationship: if an owner name was found, the borrower is the titleholder.
    if "owner_full_name" in canonical:
        owner = canonical["owner_full_name"]
        canonical["relationship_to_asset"] = FieldValue(
            value="Chủ sở hữu đứng tên trên GCN",
            confidence=0.75,
            status=FieldStatus.SUY_LUAN,
            source_doc=doc.file_name,
            source_file_id=doc.file_id,
            source_doc_type=doc.doc_type,
            source_page=owner.source_page,
            source_snippet=owner.source_snippet,
        )
    return canonical


# Per-type post-processing on top of the generic mapper.
_MAPPERS: dict[DocType, Callable[[BaseModel, IngestedDoc], dict[str, FieldValue]]] = {
    DocType.SO_DO_SO_HONG: _map_so_hong,
    DocType.TO_KHAI_LPTB: _map_extraction,
    DocType.BIEN_BAN_BAN_GIAO: _map_extraction,
    DocType.THONG_BAO_THUE_DAT: _map_extraction,
}


async def extract_node(state: IntakeState) -> dict:
    """Extract fields from supported documents into per-field candidate lists.

    Each document contributes at most one candidate :class:`FieldValue` per
    canonical key. Candidates are **not** merged here — cross-document
    reconciliation (source priority + conflict detection) happens in the merge
    node so every source is preserved for the verifier and for ``mau_thuan``.
    """
    docs: list[IngestedDoc] = state.get("docs", [])
    candidates: dict[str, list[FieldValue]] = {
        key: list(values) for key, values in state.get("candidates", {}).items()
    }
    warnings: list[str] = list(state.get("warnings", []))

    for doc in docs:
        extractor_spec = _EXTRACTORS.get(doc.doc_type)
        if extractor_spec is None:
            warnings.append(
                f"'{doc.file_name}' (loại {doc.doc_type}) chưa được hỗ trợ trích xuất (PR sau)."
            )
            continue
        if not doc.parsed.has_text:
            warnings.append(
                f"'{doc.file_name}' là bản scan — trích xuất bằng vision sẽ bổ sung ở PR sau."
            )
            continue

        schema, system_prompt = extractor_spec
        try:
            extractor = _build_extractor(schema)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Văn bản tài liệu:\n\n{doc.parsed.text}"),
            ]
            extraction = await extractor.ainvoke(messages)
        except Exception as exc:  # noqa: BLE001 - surface as a warning, don't crash the job
            logger.warning("Extraction failed for %s: %s", doc.file_name, exc)
            warnings.append(f"Trích xuất '{doc.file_name}' thất bại: {exc}")
            continue

        mapper = _MAPPERS[doc.doc_type]
        for key, fv in mapper(extraction, doc).items():
            candidates.setdefault(key, []).append(fv)

    _report_progress(state.get("ctx"), 55)
    return {"candidates": candidates, "warnings": warnings}


def _report_progress(ctx, value: int) -> None:
    cb = getattr(ctx, "update_progress", None)
    if callable(cb):
        try:
            cb(value)
        except Exception:  # pragma: no cover - progress is best-effort
            logger.debug("progress callback failed", exc_info=True)
