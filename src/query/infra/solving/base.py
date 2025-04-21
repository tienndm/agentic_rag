from __future__ import annotations

from abc import abstractmethod

from shared.base import BaseModel
from shared.base import BaseService
from shared.settings import Settings


class BaseSolvingInput(BaseModel):
    """Base input model for retriever services."""

    query: str
    top_k: int = 5
    filters: dict[str, str] | None = None
    metadata: dict[str, str] | None = None
    settings: Settings | None = None


class BaseSolvingOutput(BaseModel):
    """Base output model for retriever services."""

    results: list[dict[str, str]] = []
    metadata: dict[str, str] = {}
    error: str | None = None


class BaseSolvingService(BaseService):
    """Base class for retriever services."""

    @abstractmethod
    def process(self, input: BaseSolvingInput) -> BaseSolvingOutput:
        """Process the input and return the output."""
        raise NotImplementedError()
