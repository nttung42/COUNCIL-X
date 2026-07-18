"""LLM document classifier for the property_intake pipeline.

Replaces the PR2 keyword stub with an LLM classifier that returns the extracted
document type. Falls back to :func:`classify_by_keywords` when the text is empty
or the model call fails, so ingest never crashes on classification.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from shb.ai.llm import get_chat_model
from shb.ai.plugins.property_intake.documents import classify_by_keywords
from shb.ai.plugins.property_intake.prompts import CLASSIFY_SYSTEM
from shb.ai.plugins.property_intake.schema import DocClassification, DocType

logger = logging.getLogger(__name__)

# Only the leading portion is needed to recognise a document type; keeps the
# classification call cheap regardless of document length.
_CLASSIFY_CHAR_LIMIT = 4000


def _build_classifier():
    """Return an LLM runnable yielding a validated :class:`DocClassification`."""
    return get_chat_model().with_structured_output(DocClassification)


async def classify_document(text: str, *, classifier=None) -> DocType:
    """Classify a document's text into a :class:`DocType`.

    Uses the LLM classifier and falls back to keyword matching when the text is
    empty (e.g. an un-OCR'd scan) or the model call raises.
    """
    if not text or not text.strip():
        return classify_by_keywords(text or "")

    try:
        runnable = classifier or _build_classifier()
        result: DocClassification = await runnable.ainvoke(
            [
                SystemMessage(content=CLASSIFY_SYSTEM),
                HumanMessage(content=f"Văn bản tài liệu:\n\n{text[:_CLASSIFY_CHAR_LIMIT]}"),
            ]
        )
        return result.doc_type
    except Exception as exc:  # noqa: BLE001 - fall back rather than fail ingest
        logger.warning("LLM classification failed, falling back to keywords: %s", exc)
        return classify_by_keywords(text)
