"""Tests for AI service registry."""

import pytest
from pydantic import BaseModel, Field

from shb.ai.plugins.base import AIServiceContext, AIServiceMeta, BaseAIService
from shb.ai.plugins.registry import AIServiceRegistry


class DummyInput(BaseModel):
    name: str = Field(description="Name input")


class DummyOutput(BaseModel):
    result: str


class DummyAIService(BaseAIService):
    meta = AIServiceMeta(
        id="dummy_service",
        name="Dummy Service",
        description="A dummy service for registry testing",
        version="0.1.0",
        is_async=False,
        accepts_file=False,
    )
    InputSchema = DummyInput
    OutputSchema = DummyOutput

    async def run(self, input_data: DummyInput, ctx: AIServiceContext) -> DummyOutput:
        return DummyOutput(result="dummy")


def test_registry_register_service():
    """Test registering an AI service."""
    registry = AIServiceRegistry()
    service = DummyAIService()
    registry.register(service)

    assert registry.get("dummy_service") is not None
    assert registry.get("dummy_service").meta.id == "dummy_service"


def test_registry_duplicate_service():
    """Test registering duplicate AI service raises error."""
    registry = AIServiceRegistry()
    service1 = DummyAIService()
    service2 = DummyAIService()

    registry.register(service1)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(service2)


def test_list_services():
    """Test listing registered AI services."""
    registry = AIServiceRegistry()
    service = DummyAIService()
    registry.register(service)

    services = registry.list_services()
    assert len(services) == 1
    assert services[0].id == "dummy_service"
    assert services[0].name == "Dummy Service"


def test_get_service_schema():
    """Test getting AI service input schema."""
    registry = AIServiceRegistry()
    service = DummyAIService()
    registry.register(service)

    schema = registry.get_service_schema("dummy_service")
    assert schema is not None
    assert "properties" in schema
    assert "name" in schema["properties"]
