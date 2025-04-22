from __future__ import annotations

from pydantic import HttpUrl
from shared.base import BaseModel


class LLMSettings(BaseModel):
    """Settings for the LLM (Large Language Model)"""

    url: HttpUrl
    model: str
    frequency_penalty: int = 0
    n: int = 1
    presence_penalty: int = 0
    temperature: int = 0
    top_p: int = 1
    max_completion_tokens: int = 4096
