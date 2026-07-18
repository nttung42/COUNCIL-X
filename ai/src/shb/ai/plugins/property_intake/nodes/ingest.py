"""Ingest node: load uploaded files, parse them, and lightly classify.

Reads bytes through ``ctx.storage_service`` (never opens its own DB/engine),
parses via the hybrid :mod:`shb.services.parsers`, and tags each document with a
best-effort :class:`DocType` (keyword-based in PR2; LLM classifier in PR3).
"""

from __future__ import annotations

import logging

from shb.ai.plugins.property_intake.documents import classify_by_keywords
from shb.ai.plugins.property_intake.schema import DocumentInfo
from shb.ai.plugins.property_intake.state import IngestedDoc, IntakeState
from shb.core.config import get_settings
from shb.services.parsers import (
    DocumentParseError,
    UnsupportedFileTypeError,
    parse_upload,
)

logger = logging.getLogger(__name__)


async def ingest_node(state: IntakeState) -> dict:
    """Load + parse + classify every input file; populate ``docs``/``documents_info``."""
    ctx = state.get("ctx")
    intake_input = state["input"]
    settings = get_settings()

    storage = getattr(ctx, "storage_service", None)
    if storage is None:
        raise RuntimeError("ingest_node requires ctx.storage_service to read uploaded files.")

    docs: list[IngestedDoc] = []
    documents_info: list[DocumentInfo] = []
    warnings: list[str] = list(state.get("warnings", []))

    for file_id in intake_input.file_ids:
        file_rec = await storage.get_file(file_id)
        if file_rec is None:
            warnings.append(f"Không tìm thấy tệp '{file_id}'.")
            continue

        try:
            data = await storage.read_file(file_rec.stored_path)
            parsed = parse_upload(
                data,
                file_rec.original_name,
                file_rec.content_type,
                scan_char_threshold=settings.pdf_scan_char_threshold,
                scan_doc_fraction=settings.pdf_scan_doc_fraction,
                dpi=settings.pdf_render_dpi,
            )
        except (UnsupportedFileTypeError, DocumentParseError) as exc:
            warnings.append(f"Không đọc được tệp '{file_rec.original_name}': {exc}")
            continue

        doc_type = classify_by_keywords(parsed.text)
        docs.append(
            IngestedDoc(
                file_id=file_id,
                file_name=file_rec.original_name,
                doc_type=doc_type,
                parsed=parsed,
            )
        )
        documents_info.append(
            DocumentInfo(
                file_id=file_id,
                file_name=file_rec.original_name,
                doc_type=doc_type,
                is_scanned=parsed.is_scanned,
                page_count=parsed.page_count,
            )
        )

    _report_progress(ctx, 30)
    return {"docs": docs, "documents_info": documents_info, "warnings": warnings}


def _report_progress(ctx, value: int) -> None:
    cb = getattr(ctx, "update_progress", None)
    if callable(cb):
        try:
            cb(value)
        except Exception:  # pragma: no cover - progress is best-effort
            logger.debug("progress callback failed", exc_info=True)
