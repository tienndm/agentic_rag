from pydantic_settings import BaseSettings
from .llm import LLMSettings


class Settings(BaseSettings):
    llmSettings: LLMSettings
