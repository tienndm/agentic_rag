from __future__ import annotations

from shared.base import BaseModel


class EmbedInput(BaseModel):
    query: list[str]
