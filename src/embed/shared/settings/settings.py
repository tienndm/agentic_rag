from __future__ import annotations

from dotenv import find_dotenv
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from .embed import EmbedSettings

load_dotenv(find_dotenv('.env'), override=True)


class Settings(BaseSettings):
    """Main application settings class.

    This class uses Pydantic's BaseSettings to load configuration from
    environment variables, .env files, or other sources. It integrates
    with dotenv to automatically load environment variables from .env files.

    Attributes:
        embed (EmbedSettings): Embedding model configuration settings
    """

    embed: EmbedSettings

    class Config:
        """Pydantic configuration for the Settings class."""

        env_nested_delimiter = '__'
