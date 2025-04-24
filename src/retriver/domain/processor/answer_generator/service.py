from __future__ import annotations

from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMBaseService
from infra.llm import MessageRole
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger

from .prompt.answer_generator import SYSTEM_MESSAGE
from .prompt.answer_generator import USER_MESSAGE
"""
Answer Generator Module

This module provides functionality to generate coherent answers to user queries
using the provided context information with a language model.
"""

logger = get_logger(__name__)


class AnswerGeneratorInput(BaseModel):
    """
    Input model for the Answer Generator service.

    Attributes:
        query (str): The user's original query/question.
        context (str): Relevant context information used to generate the answer.
    """

    query: str
    context: str


class AnswerGeneratorOutput(BaseModel):
    """
    Output model for the Answer Generator service.

    Attributes:
        answer (str): The generated answer to the user's query.
        metadata (dict[str, str] | None): Optional metadata related to the answer generation.
        error (str | None): Error message if an error occurs during processing.
    """

    answer: str
    metadata: dict[str, str] | None = None
    error: str | None = None


class AnswerGenerator(BaseService):
    """
    Service responsible for generating answers to user queries using LLM.

    This service takes in a query and context information, constructs appropriate
    prompts for an LLM, and returns the generated answer.

    Attributes:
        llm_model (LLMBaseService): The language model service used for answer generation.
    """

    llm_model: LLMBaseService

    async def process(self, input: AnswerGeneratorInput) -> AnswerGeneratorOutput:
        """
        Process the input query and context to generate an answer.

        Args:
            input (AnswerGeneratorInput): The input containing the query and context.

        Returns:
            AnswerGeneratorOutput: The generated answer and associated metadata.

        Raises:
            Exception: If there's an error during message creation or answer generation.
        """
        try:
            message = [
                CompletionMessage(
                    role=MessageRole.SYSTEM,
                    content=SYSTEM_MESSAGE,
                ),
                CompletionMessage(
                    role=MessageRole.USER,
                    content=USER_MESSAGE.format(
                        query=input.query,
                        context=input.context,
                    ),
                ),
            ]
        except Exception as e:
            logger.exception(
                f'Error during creating message: {e}',
                extra={
                    'input': input,
                },
            )
            raise e

        try:
            response = await self.llm_model.process(
                LLMBaseInput(
                    messages=message,
                ),
            )

            return AnswerGeneratorOutput(
                answer=response.response,
                metadata=response.metadata,
            )
        except Exception as e:
            logger.exception(
                f'Error during generating answer: {e}',
                extra={
                    'input': input,
                },
            )
            raise e
