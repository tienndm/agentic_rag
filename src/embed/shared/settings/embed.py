from __future__ import annotations

from ..base import BaseModel


class EmbedSettings(BaseModel):
    """Configuration settings for the embedding model.

    This class defines the configuration parameters specific to the
    embedding functionality of the application.

    Attributes:
        model_name (str): Name or path of the sentence transformer model to use
    """

    model_name: str
