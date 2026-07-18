"""Endpoint chat tự do / Q&A Copilot.

RÀNG BUỘC CỨNG (contracts/appraisal-api.md mục 5): endpoint này CHỈ đọc case +
query KB + gọi LLM, rồi append vào ``chat_history_json``. TUYỆT ĐỐI không sửa
``valuation_result_json``/``risk_result_json``. Mọi câu trả lời kèm citation
``source_doc`` (Nguyên tắc II — không trả lời không nguồn).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.agents.model import chat_complete
from app.api._common import require_case
from app.orchestrator.case_store import get_store
from app.schemas import ChatMessageIn, ChatMessageOut, Citation
from app.tools.query_knowledge_base import query_knowledge_base

router = APIRouter(tags=["chat"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _retrieve(question: str, property_type: str | None) -> list[dict]:
    try:
        return query_knowledge_base(question, property_type=property_type, top_k=3)
    except Exception:  # noqa: BLE001 - KB/DB chưa sẵn sàng
        return []


def _excerpt(text: str, limit: int = 240) -> str:
    text = (text or "").strip().replace("\n", " ")
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _fallback_answer(question: str, hits: list[dict]) -> str:
    if not hits:
        return (
            "Hiện chưa truy cập được tri thức nội bộ (LLM/RAG chưa cấu hình). "
            "Đây là câu trả lời tham khảo, cần thẩm định viên kiểm chứng: "
            f"vui lòng đối chiếu quy trình thẩm định nội bộ cho câu hỏi \"{question}\"."
        )
    lines = ["Dựa trên tài liệu nội bộ (cần thẩm định viên xác nhận):"]
    for h in hits:
        lines.append(f"- ({h.get('source_doc')}) {_excerpt(h.get('chunk_text', ''))}")
    return "\n".join(lines)


@router.post("/api/cases/{case_id}/messages", response_model=ChatMessageOut)
async def post_message(case_id: str, body: ChatMessageIn) -> ChatMessageOut:
    case = require_case(case_id)  # 404 nếu không tồn tại
    store = get_store()

    sp = case.get("subject_property_json") or {}
    prop_type = sp.get("property_type")
    hits = _retrieve(body.content, prop_type)

    citations = [
        Citation(source_doc=h.get("source_doc", "?"), excerpt=_excerpt(h.get("chunk_text", "")))
        for h in hits
    ]

    context = "\n\n".join(
        f"[{h.get('source_doc')}]\n{h.get('chunk_text', '')}" for h in hits
    )
    llm_answer = chat_complete([
        {
            "role": "system",
            "content": (
                "Bạn là trợ lý thẩm định BĐS cho ngân hàng. Trả lời ngắn gọn bằng "
                "tiếng Việt, DỰA TRÊN tài liệu trích dẫn bên dưới, luôn nhắc rằng kết "
                "quả là ĐỀ XUẤT cần con người xác minh, KHÔNG tự quyết định duyệt/từ chối."
                + (f"\n\nTài liệu:\n{context}" if context else "")
            ),
        },
        {"role": "user", "content": body.content},
    ])

    answer = llm_answer or _fallback_answer(body.content, hits)

    # Append lịch sử chat — KHÔNG động tới valuation/risk (chỉ ghi chat_history_json).
    store.append_chat(case_id, {"role": "user", "content": body.content, "created_at": _now()})
    store.append_chat(case_id, {
        "role": "agent",
        "content": answer,
        "citations": [c.model_dump() for c in citations],
        "created_at": _now(),
    })

    return ChatMessageOut(role="agent", content=answer, citations=citations)
