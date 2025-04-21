from __future__ import annotations

from shared.base import BaseModel


class ApplicationInput(BaseModel):
    """Input for the application"""

    query: str


class ApplicationOutput(BaseModel):
    """Output for the application"""

    answer: str
    metadata: dict[str, str] | None = None
