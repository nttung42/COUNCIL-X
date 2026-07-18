"""LLM integration over an OpenAI-compatible endpoint (custom ``base_url``).

Endpoint, credentials and model ids are read from settings / environment and are
**never hardcoded**. Configure via ``.env`` (which is git-ignored):

* ``LLM_BASE_URL``     - base URL of the OpenAI-compatible gateway.
* ``LLM_API_KEY``      - API key for that gateway.
* ``LLM_MODEL``        - chat model id (e.g. ``cx/gpt-5.5``).
* ``LLM_VISION_MODEL`` - optional vision model id for OCR / scanned documents;
  falls back to ``LLM_MODEL`` when unset.

This module exposes:
* :func:`get_chat_model`          - text chat model.
* :func:`get_vision_model`        - vision-capable model for scans.
* :func:`build_multimodal_message` / :func:`invoke_vision` - image helpers.
"""

from __future__ import annotations

import base64
import os
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from shb.core.config import LLMSettings, get_settings

# MIME subtypes accepted for inline image content, keyed by lowercased format.
_IMAGE_MIME = {
    "png": "png",
    "jpg": "jpeg",
    "jpeg": "jpeg",
    "webp": "webp",
    "gif": "gif",
}


def _resolve_api_key(llm_config: LLMSettings) -> str:
    """Resolve the LLM API key from settings or the ``LLM_API_KEY`` env var."""
    api_key = llm_config.api_key or os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError(
            "LLM_API_KEY is required. Set it in .env or the environment "
            "(never hardcode it in code)."
        )
    return api_key


def _resolve_base_url(llm_config: LLMSettings) -> str | None:
    """Resolve the OpenAI-compatible base URL (``LLM_BASE_URL`` env wins)."""
    return os.getenv("LLM_BASE_URL") or llm_config.base_url or None


def _resolve_model(llm_config: LLMSettings) -> str:
    """Resolve the chat model id (``LLM_MODEL`` env wins over settings)."""
    return os.getenv("LLM_MODEL") or llm_config.model


def _resolve_vision_model(llm_config: LLMSettings) -> str:
    """Resolve the vision model id, falling back to the chat model."""
    return llm_config.vision_model or os.getenv("LLM_VISION_MODEL") or _resolve_model(llm_config)


def _build_config(llm_config: LLMSettings, *, model: str, base_url: str | None) -> dict:
    """Build the ChatOpenAI keyword config shared by chat and vision models."""
    config: dict = {
        "model": model,
        "temperature": llm_config.temperature,
        "max_tokens": llm_config.max_tokens,
        "max_retries": 2,
    }
    if llm_config.top_p is not None:
        config["top_p"] = llm_config.top_p
    if base_url:
        config["base_url"] = base_url
    return config


def get_chat_model() -> ChatOpenAI:
    """Get the text chat model bound to the configured OpenAI-compatible endpoint.

    Raises:
        ValueError: If the API key is missing.
    """
    llm_config = get_settings().llm
    return ChatOpenAI(
        api_key=SecretStr(_resolve_api_key(llm_config)),
        **_build_config(
            llm_config,
            model=_resolve_model(llm_config),
            base_url=_resolve_base_url(llm_config),
        ),
    )


def get_vision_model() -> ChatOpenAI:
    """Get a vision-capable model for OCR / scanned-document extraction.

    Uses ``llm.vision_model`` / ``LLM_VISION_MODEL`` and falls back to the chat
    model. Ensure the selected model actually supports image input.

    Raises:
        ValueError: If the API key is missing.
    """
    llm_config = get_settings().llm
    return ChatOpenAI(
        api_key=SecretStr(_resolve_api_key(llm_config)),
        **_build_config(
            llm_config,
            model=_resolve_vision_model(llm_config),
            base_url=_resolve_base_url(llm_config),
        ),
    )


def _image_data_uri(image: bytes, image_format: str = "png") -> str:
    """Encode raw image bytes as a base64 ``data:`` URI for inline LLM input."""
    if not image:
        raise ValueError("Cannot encode empty image bytes.")
    mime = _IMAGE_MIME.get(image_format.lower())
    if mime is None:
        raise ValueError(
            f"Unsupported image format '{image_format}'. "
            f"Supported: {', '.join(sorted(_IMAGE_MIME))}."
        )
    encoded = base64.b64encode(image).decode("ascii")
    return f"data:image/{mime};base64,{encoded}"


def build_multimodal_message(
    prompt: str,
    images: list[bytes],
    *,
    image_format: str = "png",
    detail: str = "high",
) -> HumanMessage:
    """Build a multimodal ``HumanMessage`` combining a text prompt and images.

    Args:
        prompt: Instruction / question text.
        images: Raw image bytes (e.g. rasterized scanned PDF pages). Order is
            preserved so page order is meaningful to the model.
        image_format: Image encoding of every item in ``images``.
        detail: OpenAI-style image detail hint ("high"/"low"/"auto").

    Raises:
        ValueError: If ``images`` is empty or an image cannot be encoded.
    """
    if not images:
        raise ValueError("build_multimodal_message requires at least one image.")

    content: list[Any] = [{"type": "text", "text": prompt}]
    for image in images:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": _image_data_uri(image, image_format),
                    "detail": detail,
                },
            }
        )
    return HumanMessage(content=content)


async def invoke_vision(
    prompt: str,
    images: list[bytes],
    *,
    image_format: str = "png",
    detail: str = "high",
    model: ChatOpenAI | None = None,
) -> str:
    """Invoke a vision model with a prompt and one or more images (async).

    Args:
        prompt: Instruction / question text.
        images: Raw image bytes to attach.
        image_format: Image encoding of every item in ``images``.
        detail: OpenAI-style image detail hint.
        model: Optional pre-built vision model; defaults to :func:`get_vision_model`.

    Returns:
        The model's response text.
    """
    vision = model or get_vision_model()
    message = build_multimodal_message(prompt, images, image_format=image_format, detail=detail)
    response = await vision.ainvoke([message])
    content = response.content
    return content if isinstance(content, str) else str(content)
