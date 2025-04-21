from __future__ import annotations

from shared.base import BaseModel


class RetriveInput(BaseModel):
    query: str
