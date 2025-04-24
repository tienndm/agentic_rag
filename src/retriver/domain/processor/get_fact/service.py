from __future__ import annotations

from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMBaseService
from infra.llm import MessageRole
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger

from .prompt.get_fact import SYSTEM_PROMPT
from .prompt.get_fact import USER_PROMPT
"""
Fact Extraction Service Module

This module provides functionality for extracting key facts and information
from user queries, enabling more focused and precise retrieval operations.
"""


logger = get_logger(__name__)


class GetFactInput(BaseModel):
    """
    Input model for the Fact Extraction service.

    Attributes:
        query (str): The user query from which to extract key facts.
    """

    query: str


class GetFactOutput(BaseModel):
    """
    Output model for the Fact Extraction service.

    Attributes:
        fact (str): The extracted facts from the user query.
        metadata (dict[str, str] | None): Optional metadata about the fact extraction process.
    """

    fact: str
    metadata: dict[str, str] | None = None


class GetFactService(BaseService):
    """
    Service responsible for extracting key facts from user queries.

    This service uses an LLM to analyze queries and identify the most important
    facts and information that need to be addressed. These extracted facts help
    focus subsequent retrieval operations on the most relevant information needs.

    Attributes:
        llm_model (LLMBaseService): The language model service used for fact extraction.
    """

    llm_model: LLMBaseService

    async def process(self, inputs: GetFactInput) -> GetFactOutput:
        """
        Extract key facts from the input query.

        This method constructs prompt messages for the LLM that guide it to identify
        and extract the most important facts and information needs from the user query.

        Args:
            inputs (GetFactInput): The input containing the user query.

        Returns:
            GetFactOutput: The extracted facts and associated metadata.

        Raises:
            Exception: If there's an error during message creation or fact extraction.
        """
        try:
            messages = [
                CompletionMessage(
                    role=MessageRole.SYSTEM,
                    content=SYSTEM_PROMPT,
                ),
                CompletionMessage(
                    role=MessageRole.USER,
                    content=USER_PROMPT.format(query=inputs.query),
                ),
            ]
        except Exception as e:
            logger.exception(
                f'Error during creating message: {e}',
                extra={
                    'input': inputs,
                },
            )
            raise e

        try:
            response = await self.llm_model.process(
                LLMBaseInput(
                    messages=messages,
                ),
            )
            return GetFactOutput(
                fact=response.response,
                metadata=response.metadata,
            )
        except Exception as e:
            logger.exception(
                f'Error while getting fact: {e}',
                extra={'inputs': inputs},
            )
            raise e
