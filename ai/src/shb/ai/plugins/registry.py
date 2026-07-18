"""AI Service registry with auto-discovery."""

import importlib
import inspect
from pathlib import Path
from typing import Any

from shb.ai.plugins.base import AIServiceMeta, BaseAIService


class AIServiceRegistry:
    """Registry for loading and managing AI services."""

    def __init__(self):
        self.services: dict[str, BaseAIService] = {}

    def register(self, service: BaseAIService) -> None:
        """Register an AI service instance."""
        if service.meta.id in self.services:
            raise ValueError(f"Service '{service.meta.id}' already registered")
        self.services[service.meta.id] = service

    def get(self, service_id: str) -> BaseAIService | None:
        """Get an AI service by ID."""
        return self.services.get(service_id)

    def list_services(self) -> list[AIServiceMeta]:
        """List all registered AI service metadata."""
        return [service.meta for service in self.services.values()]

    def discover_and_register(self) -> None:
        """Auto-discover and register AI services from ai/plugins directory."""
        plugins_dir = Path(__file__).parent

        for service_dir in plugins_dir.iterdir():
            if not service_dir.is_dir() or service_dir.name.startswith("_"):
                continue

            service_module_path = f"shb.ai.plugins.{service_dir.name}.service"
            try:
                module = importlib.import_module(service_module_path)
                for _, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BaseAIService)
                        and obj is not BaseAIService
                    ):
                        instance = obj()
                        self.register(instance)
            except Exception as e:
                print(f"Failed to load service from {service_module_path}: {e}")

    def get_service_schema(self, service_id: str) -> dict[str, Any] | None:
        """Get JSON schema for AI service input."""
        service = self.get(service_id)
        if not service:
            return None

        try:
            return service.InputSchema.model_json_schema()
        except Exception:
            return None


_registry = AIServiceRegistry()


def get_registry() -> AIServiceRegistry:
    """Get the global AI service registry."""
    return _registry
