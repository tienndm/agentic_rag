from __future__ import annotations

from pydantic import HttpUrl
from shared.base import BaseModel


class EmbedSettings(BaseModel):
    """Settings for the Embedding Service"""

    url: HttpUrl
