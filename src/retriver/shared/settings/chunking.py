from __future__ import annotations

from pydantic import Field
from shared.base import BaseModel


class ChunkingSettings(BaseModel):
    """Settings for the Chunking"""

    model_name: str = Field(default='sentence-transformers/all-MiniLM-L6-v2')
    similarity_threshold: float
