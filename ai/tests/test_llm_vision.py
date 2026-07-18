"""Tests for LLM config building and multimodal (vision) helpers (PR1).

These tests avoid network calls: the ChatOpenRouter constructor is replaced with
a fake that captures kwargs, and message helpers are pure functions.
"""

from __future__ import annotations

import base64
import types

import pytest

from shb.ai import llm
from shb.core.config import LLMSettings

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fake-image-body"


# --------------------------------------------------------------------------- #
# _image_data_uri
# --------------------------------------------------------------------------- #
def test_image_data_uri_png():
    """PNG bytes encode to a data URI that round-trips via base64."""
    uri = llm._image_data_uri(PNG_BYTES, "png")
    assert uri.startswith("data:image/png;base64,")
    decoded = base64.b64decode(uri.split(",", 1)[1])
    assert decoded == PNG_BYTES


def test_image_data_uri_jpg_maps_to_jpeg():
    """The jpg/JPEG formats map to the image/jpeg MIME subtype."""
    assert llm._image_data_uri(PNG_BYTES, "jpg").startswith("data:image/jpeg;base64,")
    assert llm._image_data_uri(PNG_BYTES, "JPEG").startswith("data:image/jpeg;base64,")


def test_image_data_uri_empty_raises():
    """Empty image bytes raise ValueError."""
    with pytest.raises(ValueError):
        llm._image_data_uri(b"", "png")


def test_image_data_uri_unsupported_format_raises():
    """An unsupported image format raises ValueError."""
    with pytest.raises(ValueError):
        llm._image_data_uri(PNG_BYTES, "tiff")


# --------------------------------------------------------------------------- #
# build_multimodal_message
# --------------------------------------------------------------------------- #
def test_build_multimodal_message_structure():
    """The message combines the text prompt then image content blocks."""
    msg = llm.build_multimodal_message("Extract fields", [PNG_BYTES], detail="high")
    content = msg.content
    assert content[0] == {"type": "text", "text": "Extract fields"}
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["detail"] == "high"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_build_multimodal_message_multiple_images_preserve_order():
    """Multiple images keep their input order in the message content."""
    a = b"\x89PNG\r\n\x1a\n" + b"A"
    b = b"\x89PNG\r\n\x1a\n" + b"B"
    msg = llm.build_multimodal_message("p", [a, b])
    assert len(msg.content) == 3  # text + 2 images
    assert base64.b64decode(msg.content[1]["image_url"]["url"].split(",", 1)[1]) == a
    assert base64.b64decode(msg.content[2]["image_url"]["url"].split(",", 1)[1]) == b


def test_build_multimodal_message_requires_images():
    """Building a multimodal message with no images raises ValueError."""
    with pytest.raises(ValueError):
        llm.build_multimodal_message("p", [])


# --------------------------------------------------------------------------- #
# _build_config
# --------------------------------------------------------------------------- #
def test_build_config_uses_given_model():
    """The built config uses the passed model and mirrors inference params."""
    cfg = LLMSettings(model="a/base", temperature=0.2, max_tokens=1234, top_p=0.9)
    built = llm._build_config(cfg, model="x/y", base_url=None)
    assert built["model"] == "x/y"
    assert built["temperature"] == 0.2
    assert built["max_tokens"] == 1234
    assert built["top_p"] == 0.9
    assert "base_url" not in built  # omitted when None


def test_build_config_includes_base_url():
    """A resolved base_url is passed through to the ChatOpenAI config."""
    cfg = LLMSettings(model="a/base")
    built = llm._build_config(cfg, model="a/base", base_url="https://gw/api/v1")
    assert built["base_url"] == "https://gw/api/v1"


# --------------------------------------------------------------------------- #
# get_chat_model / get_vision_model model resolution (no network)
# --------------------------------------------------------------------------- #
def _patch(monkeypatch, llm_settings: LLMSettings):
    """Replace ChatOpenAI + settings so model resolution runs offline."""
    captured: dict = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(llm, "ChatOpenAI", FakeChatOpenAI)
    monkeypatch.setattr(llm, "get_settings", lambda: types.SimpleNamespace(llm=llm_settings))
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_VISION_MODEL", raising=False)
    return captured


def test_get_chat_model_uses_base_model(monkeypatch):
    """get_chat_model resolves to the configured base model."""
    captured = _patch(monkeypatch, LLMSettings(api_key="dummy", model="m/base"))
    llm.get_chat_model()
    assert captured["model"] == "m/base"


def test_get_vision_model_prefers_vision_model(monkeypatch):
    """get_vision_model prefers the configured vision model."""
    captured = _patch(
        monkeypatch, LLMSettings(api_key="dummy", model="m/base", vision_model="v/vision")
    )
    llm.get_vision_model()
    assert captured["model"] == "v/vision"


def test_get_vision_model_falls_back_to_base(monkeypatch):
    """get_vision_model falls back to the base model when vision is unset."""
    captured = _patch(monkeypatch, LLMSettings(api_key="dummy", model="m/base", vision_model=""))
    llm.get_vision_model()
    assert captured["model"] == "m/base"


def test_get_vision_model_env_override(monkeypatch):
    """The LLM_VISION_MODEL env var overrides an empty vision_model setting."""
    captured = _patch(monkeypatch, LLMSettings(api_key="dummy", model="m/base", vision_model=""))
    monkeypatch.setenv("LLM_VISION_MODEL", "env/vision")
    llm.get_vision_model()
    assert captured["model"] == "env/vision"


def test_missing_api_key_raises(monkeypatch):
    """A missing API key raises a helpful ValueError."""
    _patch(monkeypatch, LLMSettings(api_key="", model="m/base"))
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        llm.get_chat_model()
