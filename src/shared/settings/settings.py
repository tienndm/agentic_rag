from __future__ import annotations

from pydantic_settings import BaseSettings

from .llm import LLMSettings


class Settings(BaseSettings):
    llmSettings: LLMSettings
