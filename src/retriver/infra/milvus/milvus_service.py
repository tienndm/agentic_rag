from __future__ import annotations

from typing import Any

import numpy as np
from infra.embed import EmbedInput
from infra.embed import EmbedService
from shared.base import AsyncBaseService
from shared.settings import MilvusSettings

from .milvus_driver import MilvusDriver
from .models import MilvusInput
from .models import MilvusOutput
"""
Milvus Service Module

This module provides functionality to interact with a Milvus vector database,
handling query embedding, vector similarity search, and result processing.
"""


class MilvusService(AsyncBaseService):
    """
    Service responsible for handling vector similarity searches in Milvus.

    This service manages the connection to the Milvus vector database,
    converts query text into vector embeddings, and performs similarity
    searches to retrieve relevant information.

    Attributes:
        settings (MilvusSettings): Configuration settings for the Milvus service.
        embed_service (EmbedService): Service used to generate vector embeddings.
    """

    settings: MilvusSettings
    embed_service: EmbedService

    @property
    def _driver(self):
        """
        Get the Milvus driver instance.

        Returns:
            MilvusDriver: The configured Milvus driver for database operations.
        """
        return MilvusDriver(self.settings).driver

    def execute_query(
        self,
        vector: np.ndarray,
        params: dict[str, Any] | None,
        output_format: list[str],
    ):
        """
        Execute a vector similarity search query in Milvus.

        Args:
            vector (np.ndarray): The query vector to search for.
            params (dict[str, Any] | None): Search parameters for the Milvus query.
            output_format (list[str]): Fields to include in the search results.

        Returns:
            list: The search results from Milvus, containing the most similar vectors.
        """
        result = self._driver.search(
            collection_name=self.settings.collection_name,
            anns_field=self.settings.anns_field,
            data=[vector],
            limit=self.settings.top_k,
            search_params=params,
            output_fields=output_format,
        )
        return result[0]

    async def process(self, inputs: MilvusInput) -> MilvusOutput:
        """
        Process a text query through vector similarity search.

        This method handles the complete workflow of:
        1. Converting the query text to a vector embedding
        2. Searching for similar vectors in the database
        3. Extracting and formatting the relevant results

        Args:
            inputs (MilvusInput): The input containing query text to search for.

        Returns:
            MilvusOutput: The results of the vector similarity search.

        Raises:
            Exception: If there's an error during embedding or search operations.
        """
        embed_result = await self.embed_service.process(
            EmbedInput(
                query=inputs.query,
            ),
        )
        vector = embed_result.embeddings[0]

        retrive_output = self.execute_query(
            vector=vector,
            params=self.settings.search_params,
            output_format=self.settings.output_field,
        )

        output = [
            data['entity'][str(self.settings.output_field)] for data in retrive_output
        ]

        return MilvusOutput(output=output)
