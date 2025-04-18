from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class MilvusCollection(BaseModel):
    """Model representing a Milvus collection configuration"""

    collection_name: str
    dimension: int
    metric_type: str = "COSINE"
    index_type: str = "IVF_FLAT"
    index_params: Dict[str, Any] = Field(default_factory=lambda: {"nlist": 1024})
    search_params: Dict[str, Any] = Field(default_factory=lambda: {"nprobe": 16})


class MilvusDocument(BaseModel):
    """Model representing a document to be stored in Milvus"""

    id: Optional[str] = None
    vector: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MilvusSearchResult(BaseModel):
    """Model representing a search result from Milvus"""

    id: str
    score: float
    metadata: Dict[str, Any]


class MilvusQueryResponse(BaseModel):
    """Model representing a response from a Milvus query"""

    results: List[MilvusSearchResult]
    took_ms: float


class MilvusConfig(BaseModel):
    """Configuration for Milvus connection"""

    host: str = "localhost"
    port: int = 19530
    user: Optional[str] = None
    password: Optional[str] = None
    secure: bool = False
