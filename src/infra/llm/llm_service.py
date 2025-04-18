from typing import Optional, Any

from shared.base import BaseModel, BaseService
from shared.settings import LLMSettings

from .datatypes import Message, BatchMessage, Response, BatchResponse


class LLMInput(BaseModel):
    message: Message | BatchMessage
    frequency_penalty: Optional[int] = None
    n: Optional[int] = None
    model: Optional[str] = None
    presence_penalty: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    temperature: Optional[float] = None


class LLMOutput(BaseModel):
    response: Response | BatchResponse
    metadata: dict[str, Any] = {}


class LLMService(BaseService):
    settings: LLMSettings

    @property
    def header(self) -> dict[str, str]:
        """Header for the LLM request"""
        return {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

    def process(self, input: LLMInput) -> LLMOutput:
        raise NotImplementedError("process method not implemented")
