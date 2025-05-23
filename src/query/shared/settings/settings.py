from __future__ import annotations

from dotenv import find_dotenv
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from .llm import LLMSettings
from .retrive_service import RetriveServiceSettings

load_dotenv(find_dotenv('.env'), override=True)


class Settings(BaseSettings):
    llm: LLMSettings
    retriver: RetriveServiceSettings

    class Config:
        env_nested_delimiter = '__'
