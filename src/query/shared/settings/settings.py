from __future__ import annotations

from dotenv import find_dotenv
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from .llm import LLMSettings

# from .retrive_service import RetriveServiceSettings
# from .solving_service import SolvingServiceSettings

# Load environment variables from .env file
load_dotenv(find_dotenv('.env'), override=True)


class Settings(BaseSettings):
    llm: LLMSettings

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        env_nested_delimiter = '__'
