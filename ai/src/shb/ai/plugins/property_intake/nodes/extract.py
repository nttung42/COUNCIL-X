"""Extract node: pull structured fields from each document.

PR2 supports the Sổ đỏ / Sổ hồng (GCN) type over text-based PDFs. The LLM returns
verbatim values + evidence snippets; this node then applies **grounding** (a value
whose snippet does not contain it is downgraded) and **confidence tiering** (#9)
to assign a :class:`FieldStatus`. Other document types and scanned OCR are handled
in later PRs and surface as warnings for now.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from shb.ai.llm import get_chat_model
from shb.ai.plugins.property_intake.documents import CONF_HIGH, normalize_value
from shb.ai.plugins.property_intake.prompts import SO_HONG_SYSTEM
from shb.ai.plugins.property_intake.schema import (
    DocType,
    ExtractedField,
    FieldStatus,
    FieldValue,
    SoHongExtraction,
)
from shb.ai.plugins.property_intake.state import IngestedDoc, IntakeState

logger = logging.getLogger(__name__)


def _build_extractor():
    """Return an LLM runnable that yields a validated :class:`SoHongExtraction`."""
    return get_chat_model().with_structured_output(SoHongExtraction)


def _is_grounded(value: str, snippet: str | None) -> bool:
    """Return True when a value's (normalized) text appears in its snippet."""
    if not snippet:
        return False
    norm = " ".join(value.lower().split())
    hay = " ".join(snippet.lower().split())
    return norm in hay


def _to_field_value(key: str, ef: ExtractedField | None, doc: IngestedDoc) -> FieldValue | None:
    """Map a raw extracted field to a canonical :class:`FieldValue`, or None."""
    if ef is None or not ef.value or not str(ef.value).strip():
        return None

    raw = str(ef.value).strip()
    confidence = float(ef.confidence or 0.0)

    # Grounding (feature A1): value must be traceable to its source snippet.
    if not _is_grounded(raw, ef.snippet):
        confidence = min(confidence, 0.55)

    status = FieldStatus.DA_XAC_THUC if confidence >= CONF_HIGH else FieldStatus.CAN_XAC_MINH
    return FieldValue(
        value=normalize_value(key, raw),
        confidence=round(confidence, 2),
        status=status,
        source_doc=doc.file_name,
        source_snippet=ef.snippet,
    )


def _map_so_hong(extraction: SoHongExtraction, doc: IngestedDoc) -> dict[str, FieldValue]:
    """Map a Sổ hồng extraction into canonical field values."""
    canonical: dict[str, FieldValue] = {}
    for key in SoHongExtraction.model_fields:
        fv = _to_field_value(key, getattr(extraction, key, None), doc)
        if fv is not None:
            canonical[key] = fv

    # Derive relationship: if an owner name was found, the borrower is the titleholder.
    if "owner_full_name" in canonical:
        canonical["relationship_to_asset"] = FieldValue(
            value="Chủ sở hữu đứng tên trên GCN",
            confidence=0.75,
            status=FieldStatus.SUY_LUAN,
            source_doc=doc.file_name,
            source_snippet=canonical["owner_full_name"].source_snippet,
        )
    return canonical


async def extract_node(state: IntakeState) -> dict:
    """Extract fields from supported documents into ``canonical``."""
    docs: list[IngestedDoc] = state.get("docs", [])
    canonical: dict[str, FieldValue] = dict(state.get("canonical", {}))
    warnings: list[str] = list(state.get("warnings", []))

    for doc in docs:
        if doc.doc_type != DocType.SO_DO_SO_HONG:
            warnings.append(
                f"'{doc.file_name}' (loại {doc.doc_type}) chưa được hỗ trợ trích xuất (PR sau)."
            )
            continue
        if not doc.parsed.has_text:
            warnings.append(
                f"'{doc.file_name}' là bản scan — trích xuất bằng vision sẽ bổ sung ở PR sau."
            )
            continue

        try:
            extractor = _build_extractor()
            messages = [
                SystemMessage(content=SO_HONG_SYSTEM),
                HumanMessage(content=f"Văn bản tài liệu:\n\n{doc.parsed.text}"),
            ]
            extraction = await extractor.ainvoke(messages)
        except Exception as exc:  # noqa: BLE001 - surface as a warning, don't crash the job
            logger.warning("Extraction failed for %s: %s", doc.file_name, exc)
            warnings.append(f"Trích xuất '{doc.file_name}' thất bại: {exc}")
            continue

        # PR2: single-document merge (last write wins). Cross-document
        # reconciliation with conflict detection arrives in PR4.
        canonical.update(_map_so_hong(extraction, doc))

    _report_progress(state.get("ctx"), 70)
    return {"canonical": canonical, "warnings": warnings}


def _report_progress(ctx, value: int) -> None:
    cb = getattr(ctx, "update_progress", None)
    if callable(cb):
        try:
            cb(value)
        except Exception:  # pragma: no cover - progress is best-effort
            logger.debug("progress callback failed", exc_info=True)
