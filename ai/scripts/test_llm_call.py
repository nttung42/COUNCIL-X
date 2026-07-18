#!/usr/bin/env python3
"""Quick test script for LLM integration."""

import asyncio

from dotenv import load_dotenv

from shb.ai.llm import get_chat_model

# Load environment variables
load_dotenv()


async def test_llm_basic():
    """Test basic LLM call."""
    print("🔍 Testing LLM integration...\n")

    try:
        # Get model
        print("📦 Initializing chat model...")
        model = get_chat_model()
        print(f"✓ Model initialized: {model}")

        # Test basic invoke
        print("\n📝 Testing basic invoke...")
        message = "Say 'Hello from OpenRouter!' in 5 words or less."
        response = model.invoke(message)
        print(f"Response: {response.content}\n")

        # Test with messages
        print("📝 Testing with system message...")
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage("You are a helpful AI assistant."),
            HumanMessage("What is 2+2?"),
        ]
        response = model.invoke(messages)
        print(f"Response: {response.content}\n")

        # Test streaming
        print("🔄 Testing streaming...")
        print("Response: ", end="", flush=True)
        for chunk in model.stream("Write a haiku about coding"):
            print(chunk.content, end="", flush=True)
        print("\n")

        print("✅ All tests passed!")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n📋 Setup required:")
        print("1. Set LLM_API_KEY in .env")
        print("2. Example .env:")
        print("   LLM_API_KEY=sk-or-v1-your-key")
        print("   LLM_MODEL=anthropic/claude-3-5-sonnet-20241022")
        print("   LLM_PROVIDER=openrouter")
        return False

    except Exception as e:
        print(f"❌ Test failed: {type(e).__name__}: {e}")
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(test_llm_basic())
    exit(0 if success else 1)
