from __future__ import annotations

from shared.base import BaseModel


class EmbedInput(BaseModel):
    """Input model for the embedding API endpoint.

    This model defines the expected request format for the embedding endpoint.

    Attributes:
        query (list[str]): List of text strings to be converted to embeddings
    """

    query: list[str]
