from __future__ import annotations

from dotenv import find_dotenv
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from .llm import LLMSettings
from .milvus import MilvusSettings
from .retrive import Retrive

load_dotenv(find_dotenv('.env'), override=True)


class Settings(BaseSettings):
    llm_settings: LLMSettings
    retrive_settings: Retrive
    milvus_settings: MilvusSettings

    class Config:
        env_nested_delimiter = '__'
