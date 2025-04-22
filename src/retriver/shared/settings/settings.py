from __future__ import annotations

from dotenv import find_dotenv
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from .embed import EmbedSettings
from .llm import LLMSettings
from .milvus import MilvusSettings
from .rerank import RerankSettings
from .retrive import Retrive

load_dotenv(find_dotenv('.env'), override=True)


class Settings(BaseSettings):
    llm: LLMSettings
    retrive: Retrive
    rerank: RerankSettings
    milvus_settings: MilvusSettings
    embed: EmbedSettings

    class Config:
        env_nested_delimiter = '__'
