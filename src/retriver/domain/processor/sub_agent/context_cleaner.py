from __future__ import annotations

from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMService
from infra.llm import MessageRole
from shared.logging import get_logger

from .prompt.clean_context import CLEAN_CONTEXT_SYSTEM_PROMPT
from .prompt.clean_context import CLEAN_CONTEXT_USER_PROMPT

logger = get_logger(__name__)


class ContextCleanerHandler:
    """
    Handler for cleaning and refining retrieved context to improve relevance and readability.
    """

    llm_service: LLMService
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    async def clean_context(self, step: str, context: str) -> str:
        """
        Clean and refine retrieved context to improve relevance and readability.

        Uses an LLM to filter out noise, remove redundancies, and focus on
        information that directly addresses the query.

        Args:
            step: The original query or information need
            context: The raw context to clean

        Returns:
            str: The cleaned, more focused context
        """
        messages = [
            CompletionMessage(
                role=MessageRole.SYSTEM,
                content=CLEAN_CONTEXT_SYSTEM_PROMPT,
            ),
            CompletionMessage(
                role=MessageRole.USER,
                content=CLEAN_CONTEXT_USER_PROMPT.format(query=step, context=context),
            ),
        ]
        response = await self.llm_service.process(
            LLMBaseInput(messages=messages),
        )
        context = response.response.strip()
        logger.info(f'Context cleaned: {context}')
        self.prompt_tokens += int(response.metadata['prompt_tokens'])
        self.completion_tokens += int(response.metadata['completion_tokens'])
        self.total_tokens += int(response.metadata['total_tokens'])
        return context
