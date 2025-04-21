from __future__ import annotations

from dotenv import find_dotenv
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from .embed import EmbedSettings

load_dotenv(find_dotenv('.env'), override=True)


class Settings(BaseSettings):
    embed: EmbedSettings

    class Config:
        env_nested_delimiter = '__'
