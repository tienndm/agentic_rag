from __future__ import annotations

from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMService
from infra.llm import MessageRole
from shared.base import BaseService
from shared.logging import get_logger

from .prompt.decide_tool import DECIDE_TOOL_SYSTEM_PROMPT
from .prompt.decide_tool import DECIDE_TOOL_USER_PROMPT

logger = get_logger(__name__)


class ToolDecisionHandler(BaseService):
    """
    Handler for determining which retrieval tool is most appropriate for a given information need.
    """

    llm_service: LLMService

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    async def process(self, step: str) -> str:
        """
        Determine which retrieval tool is most appropriate for a given information need.

        Uses an LLM to analyze the query and decide between vector database lookup
        or web search based on the nature of the information requested.

        Args:
            step: The processing step or query to analyze

        Returns:
            str: The selected tool name ("web_search" or "vector_db")
        """
        messages = [
            CompletionMessage(
                role=MessageRole.SYSTEM,
                content=DECIDE_TOOL_SYSTEM_PROMPT,
            ),
            CompletionMessage(
                role=MessageRole.USER,
                content=DECIDE_TOOL_USER_PROMPT.format(query=step),
            ),
        ]

        response = await self.llm_service.process(
            LLMBaseInput(messages=messages),
        )
        tool = response.response.strip().lower()
        logger.info(f'Decided to use tool: {tool} for step: {step}')
        self.prompt_tokens += int(response.metadata['prompt_tokens'])
        self.completion_tokens += int(response.metadata['completion_tokens'])
        self.total_tokens += int(response.metadata['total_tokens'])
        return tool
