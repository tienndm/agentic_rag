from __future__ import annotations

from abc import abstractmethod
from typing import Any

from shared.base import BaseModel
from shared.base import BaseService

from .datatypes import BatchMessage
from .datatypes import BatchResponse
from .datatypes import Message
from .datatypes import Response


class LLMBaseInput(BaseModel):
    messages: Message | BatchMessage


class LLMBaseOutput(BaseModel):
    response: Response | BatchResponse
    metadata: dict[str, Any] = {}


class LLMBaseService(BaseService):
    @abstractmethod
    def process(self, input: LLMBaseInput) -> LLMBaseOutput:
        raise NotImplementedError('process method not implemented')
