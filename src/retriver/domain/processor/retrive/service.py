from __future__ import annotations

from infra.milvus import MilvusInput
from infra.milvus import MilvusService
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
"""
Retrieval Service Module

This module provides functionality to retrieve relevant context information
from a vector database based on input queries.
"""


logger = get_logger(__name__)


class RetriveInput(BaseModel):
    """
    Input model for the Retrieval service.

    Attributes:
        query (list[str]): List of query strings to search for in the vector database.
    """

    query: list[str]


class RetriveOutput(BaseModel):
    """
    Output model for the Retrieval service.

    Attributes:
        context (list[str]): List of retrieved context strings relevant to the input queries.
    """

    context: list[str]


class RetriveService(BaseService):
    """
    Service responsible for retrieving relevant context from a vector database.

    This service takes in queries, uses a vector database service to find
    semantically similar content, and returns the retrieved context.

    Attributes:
        milvus_service (MilvusService): The vector database service used for retrieval.
    """

    milvus_service: MilvusService

    async def process(self, inputs: RetriveInput) -> RetriveOutput:
        """
        Process the input queries to retrieve relevant context.

        Args:
            inputs (RetriveInput): The input containing queries for the vector database.

        Returns:
            RetriveOutput: The retrieved context information.

        Raises:
            Exception: If there's an error during retrieval from the vector database.
        """
        try:
            context = self.milvus_service.process(
                MilvusInput(
                    query=inputs.query,
                ),
            )
            return RetriveOutput(context=context)
        except Exception as e:
            logger.exception(
                f'Error while retriving data from vector db: {e}',
                extra={
                    'inputs': inputs,
                },
            )
            raise e
