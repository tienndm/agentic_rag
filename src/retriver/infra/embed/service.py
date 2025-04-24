from __future__ import annotations

import httpx
import numpy as np
from shared.base import AsyncBaseService
from shared.base import BaseModel
from shared.settings import EmbedSettings
"""
Embedding Service Module

This module provides functionality to convert text into vector embeddings
using an external embedding service API.
"""


class EmbedInput(BaseModel):
    """
    Input model for the Embedding service.

    Attributes:
        query (list[str]): List of text strings to convert into embeddings.
    """

    query: list[str]


class EmbedOutput(BaseModel):
    """
    Output model for the Embedding service.

    Attributes:
        embeddings (list[np.ndarray]): List of vector embeddings corresponding to the input texts.
    """

    embeddings: list[np.ndarray]


class EmbedService(AsyncBaseService):
    """
    Service responsible for converting text into vector embeddings.

    This service communicates with an external embedding API to convert
    text strings into high-dimensional vector representations that capture
    semantic meaning, enabling semantic search and similarity comparisons.

    Attributes:
        settings (EmbedSettings): Configuration settings for the embedding service.
    """

    settings: EmbedSettings

    @property
    def header(self) -> dict[str, str]:
        """
        HTTP headers for API requests.

        Returns:
            dict[str, str]: Dictionary of HTTP headers for the embedding API requests.
        """
        return {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }

    async def process(self, inputs: EmbedInput) -> EmbedOutput:
        """
        Process text inputs into vector embeddings.

        Args:
            inputs (EmbedInput): The input containing text strings to convert to embeddings.

        Returns:
            EmbedOutput: The vector embeddings corresponding to the input texts.

        Raises:
            Exception: If there's an error during the API request or response processing.
        """
        body = {
            'query': inputs.query,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                str(self.settings.url),
                headers=self.header,
                json=body,
                timeout=None,
            )

        data = response.json()['info']['data']
        embeddings = [np.array(item['embedding']) for item in data]

        return EmbedOutput(embeddings=embeddings)
