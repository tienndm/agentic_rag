from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import Any
from typing import Optional

from shared.base import BaseModel


class BaseLLMMessage(BaseModel):
    """Base Message for LLM, all message used by LLM should inherit this model"""

    content: str


class MessageRole(str, Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'


class CompletionMessage(BaseLLMMessage):
    role: MessageRole


class StructuredOutput(BaseModel):
    name: str
    schema: dict[str, object]
    strict: bool = False
    description: Optional[str] = None


Message = Sequence[CompletionMessage]
BatchMessage = Sequence[Message]

Response = dict[str, Any] | str
BatchResponse = Sequence[Response]
