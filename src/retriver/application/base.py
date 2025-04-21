from __future__ import annotations

from shared.base import BaseModel


class ApplicationInput(BaseModel):
    query: str


class ApplicationOutput(BaseModel):
    answer: str
    metadata: dict[str, str] | None = None
