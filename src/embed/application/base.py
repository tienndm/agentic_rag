from __future__ import annotations

from shared.base import BaseModel


class ApplicationInput(BaseModel):
    query: list[str]


class ApplicationOutput(BaseModel):
    data: list[dict]
    model: str | None = None
    object: str = 'list'
    usage: dict | None = None
