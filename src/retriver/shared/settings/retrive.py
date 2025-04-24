from __future__ import annotations

from shared.base import BaseModel


class RetrieveSettings(BaseModel):
    max_tries: int
    top_k: int
