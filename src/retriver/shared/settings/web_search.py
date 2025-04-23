from __future__ import annotations

from shared.base import BaseModel


class WebSearchSettings(BaseModel):
    """Settings for the LLM (Large Language Model)"""

    headless: bool
    timeout: int

    target_tags: list[str]
    exclude_tags: list[str]
    exclude_classes: list[str]
