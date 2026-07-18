"""Advisory Agent — sinh checklist + nháp biên bản (tuần tự sau Risk).

Gọi ``query_knowledge_base`` (RAG) để lấy checklist nội bộ theo loại tài sản, rồi
``generate_report_draft`` để sinh AppraisalReportDraft. Checklist trả về (ChecklistItem
data-model.md §8) được xây từ:
  (a) các flag rủi ro cần thẩm định viên xác minh (mọi flag ``type=stigma`` -> mục
      "xác minh tin đồn dân cư", giữ ``verified=false`` ngữ nghĩa — Nguyên tắc III);
  (b) các dòng checklist trích từ KB (nếu RAG sẵn sàng).

RAG có thể chưa sẵn sàng (chưa ingest / Postgres chưa chạy) -> bọc try/except, trả
checklist rỗng phần KB, KHÔNG sập pipeline (Nguyên tắc V + Error Handling).
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.tools.generate_report_draft import generate_report_draft
from app.tools.query_knowledge_base import query_knowledge_base


def _to_dict(obj: Any) -> Any:
    """Chuyển pydantic/dataclass AppraisalReportDraft -> dict thuần."""
    if obj is None or isinstance(obj, (dict, list, str, int, float, bool)):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        try:
            return obj.dict()
        except Exception:  # noqa: BLE001
            pass
    if hasattr(obj, "__dict__"):
        return {k: _to_dict(v) for k, v in vars(obj).items()}
    return obj


def _kb_checklist_items(kb_hits: list[dict], prop_type: str, start: int) -> list[dict]:
    """Trích dòng '- [ ] ...' từ chunk KB thành ChecklistItem, giữ nguồn citation."""
    items: list[dict] = []
    idx = start
    seen: set[str] = set()
    for hit in kb_hits or []:
        source = hit.get("source_doc", "?") if isinstance(hit, dict) else "?"
        text = hit.get("chunk_text", "") if isinstance(hit, dict) else ""
        for line in text.splitlines():
            s = line.strip()
            if s.startswith(("- [ ]", "- [x]", "* [ ]", "- ")):
                content = s.split("]", 1)[1].strip() if "]" in s else s.lstrip("-* ").strip()
                if content and content not in seen:
                    seen.add(content)
                    items.append({
                        "item_id": f"kb-{idx}",
                        "text": f"{content} (nguồn: {source})",
                        "property_type_scope": [prop_type] if prop_type else [],
                        "is_checked": False,
                        "related_flag_type": None,
                    })
                    idx += 1
    return items


def _flag_checklist_items(risk_result: dict, prop_type: str) -> list[dict]:
    items: list[dict] = []
    for i, flag in enumerate(((risk_result or {}).get("flags")) or []):
        if not isinstance(flag, dict):
            continue
        ftype = flag.get("type", "khac")
        action = flag.get("action") or flag.get("detail") or "Cần thẩm định viên xác minh."
        note = " [chưa xác thực — chỉ tham khảo]" if flag.get("verified") is False else ""
        items.append({
            "item_id": f"flag-{i}",
            "text": f"{action}{note}",
            "property_type_scope": [prop_type] if prop_type else [],
            "is_checked": False,
            "related_flag_type": ftype,
        })
    return items


class AdvisoryAgent:
    async def run(
        self,
        subject_property: dict,
        valuation_result: dict,
        risk_result: dict,
    ) -> dict:
        sp = dict(subject_property or {})
        prop_type = sp.get("property_type") or "nha_pho"

        kb_hits = await asyncio.to_thread(self._query_kb, prop_type)

        draft = await asyncio.to_thread(
            generate_report_draft, sp, valuation_result, risk_result, kb_hits
        )

        checklist = _flag_checklist_items(risk_result, prop_type)
        checklist += _kb_checklist_items(kb_hits, prop_type, start=len(checklist))

        return {"checklist": checklist, "draft_report": _to_dict(draft)}

    @staticmethod
    def _query_kb(prop_type: str) -> list[dict]:
        """RAG query bọc lỗi — trả [] nếu KB/DB chưa sẵn sàng (không sập pipeline)."""
        try:
            return query_knowledge_base(
                f"checklist thẩm định tài sản bảo đảm {prop_type}",
                property_type=prop_type,
                top_k=3,
            )
        except Exception:  # noqa: BLE001
            return []


advisory_agent = AdvisoryAgent()
