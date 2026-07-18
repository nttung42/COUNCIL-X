"""Wiring model LLM OpenAI-compatible cho Google ADK + helper chat trực tiếp.

CHIẾN LƯỢC (ghi rõ để dev tái hiện — xem report):

1. ADK model: ``build_adk_model()`` bọc LLM OpenAI-compatible (base_url/api_key/model
   đọc từ ``settings``, KHÔNG hardcode — Nguyên tắc IV) qua ADK ``LiteLlm`` adapter:

       LiteLlm(model=f"openai/{settings.llm_model}", api_base=..., api_key=...)

   Trả ``None`` (không raise) nếu ADK/LiteLlm chưa cài — pipeline vẫn chạy vì
   Research/Valuation/Risk KHÔNG cần LLM (chúng gọi tool tất định). LLM chỉ cần cho
   chat Q&A (endpoint /messages) và optional cho ADK LlmAgent.

2. Chat helper: ``chat_complete()`` gọi thẳng OpenAI-compatible client cho endpoint
   Q&A Copilot. Nếu chưa cấu hình ``.env`` thật -> trả ``None`` để caller fallback
   sang câu trả lời dựa trên trích dẫn KB (degrade gracefully, không sập).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from app.config import settings


@lru_cache(maxsize=1)
def build_adk_model():
    """Trả ADK model (LiteLlm) hoặc ``None`` nếu ADK/LiteLlm không khả dụng."""
    try:
        from google.adk.models.lite_llm import LiteLlm
    except Exception:  # noqa: BLE001 - ADK chưa cài / API khác version
        return None
    try:
        return LiteLlm(
            model=f"openai/{settings.llm_model}",
            api_base=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )
    except Exception:  # noqa: BLE001
        return None


def adk_available() -> bool:
    try:
        import google.adk  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False


@lru_cache(maxsize=1)
def _openai_client():
    from openai import OpenAI

    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


def chat_complete(
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int = 700,
) -> Optional[str]:
    """Gọi chat completion OpenAI-compatible; ``None`` nếu LLM chưa cấu hình.

    Không raise ra ngoài — endpoint chat sẽ fallback sang trả lời dựa trên KB.
    """
    try:
        resp = _openai_client().chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:  # noqa: BLE001 - endpoint/API key chưa sẵn sàng
        return None
