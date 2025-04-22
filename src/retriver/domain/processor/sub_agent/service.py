from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List

from domain.processor.rerank import RerankInput
from domain.processor.rerank import RerankService
from domain.processor.retrive import RetriveInput
from domain.processor.retrive import RetriveOutput
from domain.processor.retrive import RetriveService
from domain.processor.web_searching import WebSearchingInput
from domain.processor.web_searching import WebSearchingOutput
from domain.processor.web_searching import WebSearchService
from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMService
from infra.llm import MessageRole
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import Settings

from .prompt.clean_context import CLEAN_CONTEXT_SYSTEM_PROMPT
from .prompt.clean_context import CLEAN_CONTEXT_USER_PROMPT
from .prompt.decide_tool import DECIDE_TOOL_SYSTEM_PROMPT
from .prompt.decide_tool import DECIDE_TOOL_USER_PROMPT

logger = get_logger(__name__)


class SubAgentInput(BaseModel):
    """Input model for the SubAgent service."""

    step: str


class SubAgentOutput(BaseModel):
    """Output model for the SubAgent service."""

    info: str
    metadata: Dict[str, str] | None = None


class SubAgentService(BaseService):
    """Service for handling sub-agent operations, including tool selection and context retrieval."""

    settings: Settings
    llm_service: LLMService
    web_search_service: WebSearchService
    retrive_service: RetriveService
    rerank_service: RerankService

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    async def decide_tool(self, step: str) -> str:
        """Determine which tool to use for processing a given step.

        Args:
            step: The processing step/query

        Returns:
            The selected tool name
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

    async def clean_context(self, step: str, context: str) -> str:
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
        self.prompt_tokens += response.metadata['prompt_tokens']
        self.completion_tokens += response.metadata['completion_tokens']
        self.total_tokens += response.metadata['total_tokens']
        return context

    async def handle_web_search(self, step: str) -> WebSearchingOutput:
        """Handle web search for a given step.

        Args:
            step: The search query

        Returns:
            WebSearchingOutput with search results
        """
        return await self.web_search_service.process(
            WebSearchingInput(
                query=step,
                top_k=self.settings.retrive.top_k,
            ),
        )

    async def handle_retriver(self, step: str) -> RetriveOutput:
        """Handle vector database query for a given step.

        Args:
            step: The search query

        Returns:
            RetriveOutput with search results
        """
        return await self.retrive_service.process(
            RetriveInput(
                query=step,
            ),
        )

    async def handle_tool(self, tool: str, step: str) -> List[Dict[str, Any]]:
        """Process a step using the selected tool.

        Args:
            tool: The tool to use ("web_search" or "vector_db")
            step: The processing step/query

        Returns:
            List of context dictionaries

        Raises:
            ValueError: If an unsupported tool is specified
        """
        contexts = []

        if tool == 'web_search':
            web_search_output = await self.handle_web_search(step=step)
            contexts = web_search_output.contexts

        elif tool == 'vector_db':
            vector_db_output = self.handle_retriver(step=step)
            for context in vector_db_output.context:
                contexts.append({'content': context})

        else:
            logger.error(f'Unsupported tool selected: {tool}')
            raise ValueError(f'Unsupported tool: {tool}')

        logger.info(f'Contexts retrive: {contexts}')

        return contexts

    async def process(self, inputs: SubAgentInput) -> SubAgentOutput:
        """Process a step using the appropriate tool and generate a consolidated response.

        Args:
            inputs: The SubAgentInput containing the step to process

        Returns:
            SubAgentOutput with consolidated information and metadata
        """

        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

        try:
            tool = await self.decide_tool(inputs.step)
        except Exception as e:
            logger.exception(
                f'Error while deciding tool: {e}',
                extra={
                    'inputs': inputs,
                },
            )
            raise

        try:
            contexts = await self.handle_tool(tool=tool, step=inputs.step)
        except Exception as e:
            logger.exception(f'Error while using tool: {e}', extra={'inputs': inputs})

        try:
            rerank_input = RerankInput(
                query=inputs.step,
                contexts=contexts,
                top_k=self.settings.retrive.top_k or 3,
            )

            rerank_output = await self.rerank_service.process(rerank_input)
            contexts = rerank_output.ranked_contexts
        except Exception as e:
            logger.exception(
                f'Error while reranking: {e}',
                extra={
                    'inputs': inputs,
                    'contexts_count': len(contexts),
                },
            )
            raise e

        try:
            context = self.clean_context(
                step=inputs.step,
                context=str(contexts),
            )
        except Exception as e:
            logger.exception(
                f'Error while cleaned context: {e}',
                extra={
                    'inputs': inputs,
                },
            )
            raise

        return SubAgentOutput(
            info=context,
            metadata={
                'prompt_tokens': self.prompt_tokens,
                'completion_tokens': self.completion_tokens,
                'total_tokens': self.total_tokens,
            },
        )
