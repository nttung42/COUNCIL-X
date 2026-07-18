"""Prompt caching support for OpenRouter.

OpenRouter forwards cache_control markers to underlying providers like
Anthropic, OpenAI, and Gemini, enabling prompt caching uniformly.

Convention:
- Stable/reusable content (rules, system context) in SystemMessage with cache marker
- Per-request data (user input, specific details) in HumanMessage
"""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from shb.core.config import get_settings


def cached_system(system_prompt: str) -> SystemMessage:
    """Create a SystemMessage with OpenRouter prompt cache marker.

    When prompt caching is enabled, tags the system prompt with an ephemeral
    cache control marker so providers can cache the system instructions.

    Args:
        system_prompt: The system message content

    Returns:
        SystemMessage (with cache marker if enabled, plain otherwise)
    """
    settings = get_settings()

    if not settings.llm.enable_prompt_cache:
        return SystemMessage(content=system_prompt)

    return SystemMessage(
        content=[
            {"type": "text", "text": "system"},
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            },
        ]
    )


def build_cached_messages(system_prompt: str, user_prompt: str) -> list[Any]:
    """Build message list with cached system prompt.

    Args:
        system_prompt: Reusable system instructions (will be cached if enabled)
        user_prompt: User input (not cached, changes per request)

    Returns:
        List of [cached SystemMessage, HumanMessage]
    """
    return [cached_system(system_prompt), HumanMessage(content=user_prompt)]
