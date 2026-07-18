"""Base AI Service interface and plugin architecture."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel


@dataclass
class AIServiceMeta:
    """Metadata for an AI service."""

    id: str
    name: str
    description: str
    version: str = "0.1.0"
    is_async: bool = False
    accepts_file: bool = False
    file_types: list[str] = field(default_factory=list)


@dataclass
class AIServiceContext:
    """Context passed to AI services during execution."""

    user_id: str
    service_id: str
    job_id: str | None = None
    update_progress: Callable[[int], None] | None = None
    llm_client: Any = None
    storage_service: Any = None
    # Factory returning an AsyncSession context manager (e.g. AsyncSessionLocal).
    # Injected by the worker/API so DB-reading services (e.g. property_lookup)
    # can open their own session without importing the engine directly.
    db_session_factory: Any = None


class BaseAIService(ABC):
    """Abstract base class for all AI services."""

    meta: AIServiceMeta
    InputSchema: type[BaseModel]
    OutputSchema: type[BaseModel]

    @abstractmethod
    async def run(self, input_data: BaseModel, ctx: AIServiceContext) -> BaseModel:
        """Execute the AI service.

        For complex services, this can delegate to a LangGraph graph.
        """
        pass
