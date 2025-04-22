from __future__ import annotations

from shared.base import BaseModel


class RerankSettings(BaseModel):
    """Settings for the Reranking service"""

    model_name: str
