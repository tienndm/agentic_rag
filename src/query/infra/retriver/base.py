from __future__ import annotations

from abc import abstractmethod

from shared.base import BaseModel
from shared.base import BaseService


class BaseRetriveInput(BaseModel):
    """Base input model for retriever services."""

    query: str


class BaseRetriveOutput(BaseModel):
    """Base output model for retriever services."""

    answer: str
    metadata: dict[str, str] = {}


class BaseRetriveService(BaseService):
    """Base class for retriever services."""

    @abstractmethod
    def process(self, input: BaseRetriveInput) -> BaseRetriveOutput:
        """Process the input and return the output."""
        raise NotImplementedError()
