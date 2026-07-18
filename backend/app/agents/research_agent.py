"""Research Agent — chạy 7 lookup tool SONG SONG (SC-001: pipeline < 15s).

CHIẾN LƯỢC WIRING (ghi rõ trong report):
- Chọn ``asyncio.gather`` + ``asyncio.to_thread`` làm cơ chế CHÍNH: 7 lookup tool
  là hàm SYNC (đọc mock JSON, I/O-bound). ``to_thread`` đẩy chúng ra thread pool ->
  chạy ĐỒNG THỜI thật sự, không tuần tự. Đây là fallback "chắc chắn chạy" mà skill
  đã cho phép, KHÔNG cần LLM endpoint sống (Research là bước tất định).
- ADK ``ParallelAgent`` được dựng "best-effort" ở ``build_adk_parallel_agent()`` cho
  đúng idiom ADK khi có model; nhưng KHÔNG dùng để chạy pipeline (tránh phụ thuộc
  LLM). Xem report.

1 tool lỗi/timeout KHÔNG làm sập cả bước: mỗi tool bọc try/except, trả envelope
``status="error"`` để pipeline tiếp tục (spec.md Edge Case + Nguyên tắc V).
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from app.tools import (
    environmental_risk_lookup,
    legal_status_lookup,
    liquidity_stat_lookup,
    market_price_lookup,
    neighborhood_amenity_lookup,
    planning_zoning_lookup,
    stigma_reputation_lookup,
)

# Key kết quả -> (tool, hàm dựng kwargs từ subject_property).
# Key khớp contracts/appraisal-api.md mục 3 (lookup_result.market_price, ...).
_TOOLS: dict[str, tuple[Callable[..., dict], Callable[[dict], dict]]] = {
    "market_price": (
        market_price_lookup,
        lambda sp: {
            "address": sp.get("address"),
            "lat": sp.get("lat"),
            "long": sp.get("long"),
            "property_type": sp.get("property_type"),
        },
    ),
    "planning_zoning": (
        planning_zoning_lookup,
        lambda sp: {"address": sp.get("address"), "cadastral_id": sp.get("cadastral_id")},
    ),
    "legal_status": (
        legal_status_lookup,
        lambda sp: {"address": sp.get("address"), "owner_id": sp.get("owner_id")},
    ),
    "neighborhood_amenity": (
        neighborhood_amenity_lookup,
        lambda sp: {"lat": sp.get("lat"), "long": sp.get("long")},
    ),
    "stigma_reputation": (
        stigma_reputation_lookup,
        lambda sp: {"address": sp.get("address")},
    ),
    "environmental_risk": (
        environmental_risk_lookup,
        lambda sp: {"lat": sp.get("lat"), "long": sp.get("long")},
    ),
    "liquidity_stat": (
        liquidity_stat_lookup,
        lambda sp: {
            "address": sp.get("address"),
            "ward": sp.get("ward"),
            "property_type": sp.get("property_type") or "nha_pho",
        },
    ),
}


def _error_envelope(tool_name: str, exc: Exception) -> dict:
    return {
        "tool_name": tool_name,
        "status": "error",
        "confidence": 0.0,
        "source_type": "mock",
        "data": {},
        "warning": f"Lỗi khi chạy {tool_name}: {exc}",
    }


async def _run_one(key: str, sp: dict) -> tuple[str, dict]:
    tool, build_kwargs = _TOOLS[key]
    try:
        kwargs = build_kwargs(sp)
        # to_thread -> chạy song song thật cho hàm sync I/O-bound.
        env = await asyncio.to_thread(tool, **kwargs)
        if not isinstance(env, dict):
            env = _error_envelope(getattr(tool, "__name__", key), ValueError("non-dict"))
        return key, env
    except Exception as exc:  # noqa: BLE001 - cô lập lỗi từng tool
        return key, _error_envelope(getattr(tool, "__name__", key), exc)


class ResearchAgent:
    """Điều phối 7 lookup tool song song, trả dict envelope theo key."""

    async def run(self, subject_property: dict) -> dict[str, dict]:
        sp = dict(subject_property or {})
        results = await asyncio.gather(*[_run_one(k, sp) for k in _TOOLS])
        return {k: env for k, env in results}


research_agent = ResearchAgent()


# --------------------------------------------------------------------------- #
# Best-effort ADK ParallelAgent (idiom) — KHÔNG dùng để chạy pipeline.
# --------------------------------------------------------------------------- #
def build_adk_parallel_agent() -> Any:
    """Dựng ADK ParallelAgent bọc 7 lookup (nếu ADK + model khả dụng), else None.

    Chỉ để minh hoạ đúng idiom ADK / mở đường nâng cấp; pipeline thực tế dùng
    ``ResearchAgent.run`` (asyncio.gather) cho chắc chắn & không cần LLM.
    """
    try:
        from google.adk.agents import LlmAgent, ParallelAgent

        from app.agents.model import build_adk_model

        model = build_adk_model()
        if model is None:
            return None
        sub_agents = [
            LlmAgent(name=key, model=model, tools=[tool])
            for key, (tool, _) in _TOOLS.items()
        ]
        return ParallelAgent(name="research_agent", sub_agents=sub_agents)
    except Exception:  # noqa: BLE001
        return None
