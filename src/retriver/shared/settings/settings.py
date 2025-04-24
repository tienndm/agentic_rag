from __future__ import annotations

from dotenv import find_dotenv
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from .chunking import ChunkingSettings
from .embed import EmbedSettings
from .llm import LLMSettings
from .milvus import MilvusSettings
from .rerank import RerankSettings
from .retrive import RetriveSettings
from .web_search import WebSearchSettings

load_dotenv(find_dotenv('.env'), override=True)


class Settings(BaseSettings):
    llm: LLMSettings
    embed: EmbedSettings
    retrive: RetriveSettings
    rerank: RerankSettings
    milvus: MilvusSettings
    web_search: WebSearchSettings
    chunking: ChunkingSettings

    class Config:
        env_nested_delimiter = '__'
