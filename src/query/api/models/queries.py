from __future__ import annotations

from shared.base import BaseModel


class QuerierInput(BaseModel):
    query: str


class QuerierOutput(BaseModel):
    answer: str = ''
