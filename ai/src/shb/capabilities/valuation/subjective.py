"""LLM subjective valuation adjustment (hướng nhà / phong thủy / vị trí).

The ONLY non-deterministic input to the valuation engine. Returns a bounded
fraction (±``bound``, default ±5%) plus a human-readable reason, clearly tagged as
an LLM inference. **Fail-safe**: any model error yields ``0.0`` so the valuation
still runs purely from the formula (audit invariant).
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from shb.ai.llm import get_chat_model

logger = logging.getLogger(__name__)

SUBJECTIVE_SYSTEM = """\
Bạn là chuyên gia định giá BĐS Việt Nam, đánh giá các yếu tố CẢM TÍNH ảnh hưởng
giá trị mà công thức định lượng KHÔNG nắm được: hướng nhà, phong thủy, vị trí
(góc, nở hậu/tóp hậu, gần yếu tố bất lợi…).

NHIỆM VỤ: trả về:
- "adjustment_pct": hệ số điều chỉnh giá theo yếu tố cảm tính, đơn vị PHẦN TRĂM,
  trong khoảng [-5, +5]. Dương = tăng giá (hướng đẹp, vị trí tốt); âm = giảm.
- "reason": lý do ngắn gọn (1–2 câu).

QUY TẮC:
1. TUYỆT ĐỐI không vượt ngoài [-5, +5]. Đa số trường hợp bình thường nên gần 0.
2. Chỉ xét yếu tố cảm tính — KHÔNG lặp lại yếu tố đã có trong công thức (diện tích,
   giá so sánh, số tầng, tuổi, lộ giới…).
3. Đây là ý kiến tham khảo, không phải phán quyết — thận trọng, không thổi phồng.
"""


class SubjectiveAssessment(BaseModel):
    """LLM verdict on the subjective price adjustment."""

    adjustment_pct: float = Field(
        ...,
        description="Điều chỉnh giá do yếu tố cảm tính, đơn vị %, trong [-5, +5].",
    )
    reason: str = Field(..., description="Lý do ngắn gọn.")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


async def assess_subjective_adjustment(
    features: dict, *, bound: float = 0.05, assessor=None
) -> tuple[float, str]:
    """Return ``(adjustment_fraction, reason)`` for a property's subjective factors.

    ``features`` is a dict of the qualitative fields (house_direction, address,
    road_type, structure, notes…). ``bound`` caps the magnitude. On any LLM error
    the adjustment is ``0.0`` (fail-safe) so the formula-only valuation stands.
    """
    prompt = "Đặc điểm tài sản:\n" + "\n".join(
        f"- {k}: {v}" for k, v in features.items() if v not in (None, "")
    )
    try:
        runnable = assessor or get_chat_model().with_structured_output(SubjectiveAssessment)
        result: SubjectiveAssessment = await runnable.ainvoke(
            [SystemMessage(content=SUBJECTIVE_SYSTEM), HumanMessage(content=prompt)]
        )
        fraction = _clamp(result.adjustment_pct / 100.0, -bound, bound)
        return fraction, result.reason
    except Exception as exc:  # noqa: BLE001 - fail-safe: valuation must still run
        logger.warning("subjective adjustment failed, using 0%%: %s", exc)
        return 0.0, "Không đánh giá được yếu tố cảm tính — dùng 0% (chỉ định giá theo công thức)."
