from __future__ import annotations

from shared.base import BaseModel


class RetriveServiceSettings(BaseModel):
    """Settings for the LLM (Large Language Model)"""

    model: str
    top_k: int = 5
    frequency_penalty: int = 0
    n: int
    presence_penalty: int = 0
    temperature: float = 0
    top_p: int = 1
    max_completion_tokens: int = 4096
