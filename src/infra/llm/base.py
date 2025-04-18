from __future__ import annotations

from abc import abstractmethod
from typing import Any
from typing import Optional

from shared.base import BaseModel
from shared.base import BaseService

from .datatypes import BatchMessage
from .datatypes import BatchResponse
from .datatypes import Message
from .datatypes import Response


class LLMBaseInput(BaseModel):
    message: Message | BatchMessage
    frequency_penalty: Optional[int] = None
    n: Optional[int] = None
    model: Optional[str] = None
    presence_penalty: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    temperature: Optional[float] = None


class LLMBaseOutput(BaseModel):
    response: Response | BatchResponse
    metadata: dict[str, Any] = {}


class LLMBaseService(BaseService):
    @abstractmethod
    def process(self, input: LLMBaseInput) -> LLMBaseOutput:
        raise NotImplementedError('process method not implemented')
