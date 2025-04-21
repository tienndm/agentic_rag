from __future__ import annotations

import os

from pydantic import HttpUrl
from shared.base import BaseModel


class LLMSettings(BaseModel):
    """Settings for the LLM (Large Language Model)"""

    url: HttpUrl = os.getenv(
        'LLM_ENDPOINT', 'https://bc29-34-75-14-44.ngrok-free.app/v1/chat/completions',
    )
    model: str = os.getenv('LLM_MODEL', '')
    frequency_penalty: int = int(os.getenv('LLM_FREQUENCY_PENALTY', '0'))
    n: int = int(os.getenv('LLM_N', '1'))
    presence_penalty: int = int(os.getenv('LLM_PRESENCE_PENALTY', '0'))
    temperature: float = float(os.getenv('LLM_TEMPERATURE', '0'))
    top_p: int = int(os.getenv('LLM_TOP_P', '1'))
    max_completion_tokens: int = int(os.getenv('LLM_MAX_COMPLETION_TOKENS', '4096'))
