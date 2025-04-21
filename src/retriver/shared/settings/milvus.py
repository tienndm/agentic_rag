from __future__ import annotations

import os
from typing import Any
from typing import Dict
from typing import Optional

from pydantic import Field

from ..base import BaseModel


class MilvusSettings(BaseModel):
    host: str = os.getenv('MILVUS_HOST', 'localhost')
    port: int = int(os.getenv('MILVUS_PORT', '19530'))
    user: Optional[str] = os.getenv('MILVUS_USER')
    password: Optional[str] = os.getenv('MILVUS_PASSWORD')
    secure: bool = os.getenv('MILVUS_SECURE', 'False').lower() == 'true'

    search_params: Dict[str, Any] = Field(default_factory=lambda: {'nprobe': 16})
    top_k: int = 3
