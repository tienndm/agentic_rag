from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Optional

from pydantic import Field

from ..base import BaseModel


class MilvusSettings(BaseModel):
    host: str
    port: int
    user: Optional[str] = None
    password: Optional[str] = None
    db_name: str
    collection_name: str
    anns_field: str
    output_field: list[str]

    search_params: Dict[str, Any] = Field(default_factory=lambda: {'nprobe': 16})
    top_k: int = 3
