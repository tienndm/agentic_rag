from __future__ import annotations

from shared.base import BaseModel


class MilvusInput(BaseModel):
    query: str


class MilvusOutput(BaseModel):
    output: list[str]
