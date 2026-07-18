"""Embedding helper — gọi embedding model qua OpenAI-compatible client.

KHÔNG hardcode base_url / api_key / model — luôn đọc qua `app.config.settings`
(Nguyên tắc IV, Technical Context của plan.md). Client được khởi tạo lazy để
việc import module KHÔNG yêu cầu `.env` thật (cho phép test chunking offline).
"""

from __future__ import annotations

from functools import lru_cache

from app.config import settings

# Giá trị mặc định trong config.py khi chưa điền `.env` thật (xem
# backend/app/config.py / backend/.env.example). Dùng để short-circuit,
# tránh việc gọi mạng vô ích (rồi chờ timeout) khi rõ ràng chưa cấu hình LLM
# thật — quick-start path (không Docker/không .env) phải trả lời gần như tức
# thời thay vì luôn mất vài giây chờ 1 request chắc chắn sẽ fail.
_PLACEHOLDER_API_KEY = "sk-placeholder-not-set"


def _is_configured() -> bool:
    return bool(settings.llm_api_key) and settings.llm_api_key != _PLACEHOLDER_API_KEY


@lru_cache(maxsize=1)
def _get_client():
    """Khởi tạo OpenAI-compatible client 1 lần (lazy).

    Tách riêng để lỗi thiếu SDK/`.env` chỉ phát sinh khi thực sự gọi embedding,
    không chặn import (ingest có thể test chunking mà không cần endpoint thật).
    """
    from openai import OpenAI

    # Short timeout + no retries: when the embedding endpoint isn't configured
    # yet (quick-start path, no real LLM), fail fast instead of hanging the
    # request close to the client's own timeout (SC-001, <15s pipeline).
    return OpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        timeout=5.0,
        max_retries=0,
    )


def embed_text(text: str) -> list[float]:
    """Trả về embedding vector của `text`.

    Raises:
        RuntimeError: khi endpoint/`.env` chưa cấu hình được (bọc lỗi API rõ ràng
            để caller/ingest xử lý — cần `.env` thật để chạy). Trả về ngay lập
            tức (không gọi mạng) nếu `LLM_API_KEY` vẫn là giá trị placeholder.
    """
    if not _is_configured():
        raise RuntimeError(
            "LLM_API_KEY chưa được cấu hình (.env) — bỏ qua gọi embedding endpoint. "
            "Điền LLM_BASE_URL/LLM_API_KEY/EMBEDDING_MODEL trong backend/.env để bật RAG."
        )
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
    if not _is_configured():
        raise RuntimeError(
            "LLM_API_KEY chưa được cấu hình (.env) — bỏ qua gọi embedding endpoint. "
            "Điền LLM_BASE_URL/LLM_API_KEY/EMBEDDING_MODEL trong backend/.env để bật RAG."
        )
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
