"""LLM narrator for the Màn 5 Dashboard — prose only, bounded, fail-safe.

The 4 "Tổng hợp theo từng bước" summaries + the overall conclusion are built
deterministically as templates from the Màn 1–4 facts (numbers/decision come
from the engines, never the LLM). The LLM's ONLY job is to REWORD those
templates into fluent Vietnamese — it must not change any number, name or
decision, nor add facts. **Fail-safe**: any model error (or no model) returns the
templates verbatim, tagged ``generated_by="template"``. See dashboard-methodology.md.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from shb.ai.llm import get_chat_model

logger = logging.getLogger(__name__)

NARRATOR_SYSTEM = """\
Bạn là trợ lý biên tập cho báo cáo thẩm định tài sản của ngân hàng. Bạn được cung
cấp các đoạn tóm tắt THÔ (đã chứa đầy đủ số liệu và kết luận) cho từng bước và một
đoạn kết luận chung.

NHIỆM VỤ: viết lại cho mượt, rõ ràng, đúng văn phong nghiệp vụ tiếng Việt.

QUY TẮC BẮT BUỘC:
1. TUYỆT ĐỐI không thay đổi bất kỳ con số, tỷ lệ %, số tiền, nhãn rủi ro hay
   quyết định cho vay nào. Giữ nguyên chính xác như đầu vào.
2. KHÔNG thêm dữ kiện, giả định hay khuyến nghị mới không có trong đầu vào.
3. Mỗi đoạn ngắn gọn (1–3 câu). Trả về đúng số đoạn theo thứ tự đã cho.
"""


@dataclass
class StepFact:
    """One dashboard step: its title + the deterministic template text (fallback + facts)."""

    step_number: int
    title: str
    template_text: str


@dataclass
class DashboardFacts:
    """Deterministic facts fed to the narrator (also the fail-safe output)."""

    steps: list[StepFact] = field(default_factory=list)
    overall_template: str = ""


@dataclass
class DashboardNarration:
    """Narrated output — step summaries (step_number, text) + overall + provenance."""

    step_summaries: list[tuple[int, str]]
    overall_narrative: str
    generated_by: str  # "llm" | "template"


class _NarrationOut(BaseModel):
    """Structured LLM response — same length/order as the input steps."""

    step_summaries: list[str] = Field(..., description="Các đoạn tóm tắt đã viết lại, đúng thứ tự.")
    overall_narrative: str = Field(..., description="Đoạn kết luận chung đã viết lại.")


def _template(facts: DashboardFacts) -> DashboardNarration:
    return DashboardNarration(
        step_summaries=[(s.step_number, s.template_text) for s in facts.steps],
        overall_narrative=facts.overall_template,
        generated_by="template",
    )


async def narrate_dashboard(facts: DashboardFacts, *, narrator=None) -> DashboardNarration:
    """Reword the deterministic step/overall templates into fluent Vietnamese.

    ``narrator`` is an optional structured-output runnable (injected in tests);
    when omitted a chat model is built lazily. On ANY error, or if the model
    returns the wrong number of steps, the untouched templates are returned
    (fail-safe) — so the dashboard always has coherent, number-accurate text.
    """
    if not facts.steps:
        return _template(facts)

    prompt = (
        "CÁC ĐOẠN CẦN VIẾT LẠI (giữ nguyên mọi số liệu/quyết định):\n\n"
        + "\n".join(f"[Bước {s.step_number} — {s.title}]\n{s.template_text}" for s in facts.steps)
        + f"\n\n[Kết luận chung]\n{facts.overall_template}"
    )

    try:
        runnable = narrator or get_chat_model().with_structured_output(_NarrationOut)
        result: _NarrationOut = await runnable.ainvoke(
            [SystemMessage(content=NARRATOR_SYSTEM), HumanMessage(content=prompt)]
        )
        if len(result.step_summaries) != len(facts.steps):
            raise ValueError("step count mismatch from narrator")
        return DashboardNarration(
            step_summaries=[
                (facts.steps[i].step_number, text.strip() or facts.steps[i].template_text)
                for i, text in enumerate(result.step_summaries)
            ],
            overall_narrative=result.overall_narrative.strip() or facts.overall_template,
            generated_by="llm",
        )
    except Exception as exc:  # noqa: BLE001 - fail-safe: dashboard must still render
        logger.warning("dashboard narration failed, using templates: %s", exc)
        return _template(facts)
