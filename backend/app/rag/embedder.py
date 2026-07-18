"""Embedding helper — gọi embedding model qua OpenAI-compatible client.

KHÔNG hardcode base_url / api_key / model — luôn đọc qua `app.config.settings`
(Nguyên tắc IV, Technical Context của plan.md). Client được khởi tạo lazy để
việc import module KHÔNG yêu cầu `.env` thật (cho phép test chunking offline).
"""

from __future__ import annotations

from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def _get_client():
    """Khởi tạo OpenAI-compatible client 1 lần (lazy).

    Tách riêng để lỗi thiếu SDK/`.env` chỉ phát sinh khi thực sự gọi embedding,
    không chặn import (ingest có thể test chunking mà không cần endpoint thật).
    """
    from openai import OpenAI

    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


def embed_text(text: str) -> list[float]:
    """Trả về embedding vector của `text`.

    Raises:
        RuntimeError: khi endpoint/`.env` chưa cấu hình được (bọc lỗi API rõ ràng
            để caller/ingest xử lý — cần `.env` thật để chạy).
    """
    try:
        resp = _get_client().embeddings.create(
            model=settings.embedding_model,
            input=text,
        )
        return resp.data[0].embedding
    except Exception as exc:  # noqa: BLE001 - bọc mọi lỗi API/SDK thành thông báo rõ
        raise RuntimeError(
            "Không gọi được embedding endpoint. Kiểm tra LLM_BASE_URL / LLM_API_KEY "
            f"/ EMBEDDING_MODEL trong .env. Chi tiết: {exc}"
        ) from exc


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch embedding — 1 lời gọi API cho nhiều đoạn (ingest dùng để tiết kiệm)."""
    if not texts:
        return []
    try:
        resp = _get_client().embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
        # OpenAI trả về theo đúng thứ tự input, nhưng sort theo index cho chắc.
        ordered = sorted(resp.data, key=lambda d: d.index)
        return [d.embedding for d in ordered]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Không gọi được embedding endpoint (batch). Kiểm tra .env. "
            f"Chi tiết: {exc}"
        ) from exc
