from __future__ import annotations

from pydantic import HttpUrl
from shared.base import BaseModel


class RetriveServiceSettings(BaseModel):
    """Settings for the LLM (Large Language Model)"""

    url: HttpUrl
