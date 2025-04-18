from abc import abstractmethod
from typing import Optional, Any

from shared.base import BaseModel, BaseService
from shared.settings import LLMSettings

from .datatypes import Message, BatchMessage, Response, BatchResponse


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
        raise NotImplementedError("process method not implemented")
