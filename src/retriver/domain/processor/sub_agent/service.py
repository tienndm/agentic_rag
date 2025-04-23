from __future__ import annotations

import json
from typing import Any
from typing import Dict
from typing import List

from domain.processor.rerank import RerankInput
from domain.processor.rerank import RerankService
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
from .prompt.validate_output import VALIDATE_OUTPUT_SYSTEM_PROMPT
from .prompt.validate_output import VALIDATE_OUTPUT_USER_PROMPT

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
        self.prompt_tokens += int(response.metadata['prompt_tokens'])
        self.completion_tokens += int(response.metadata['completion_tokens'])
        self.total_tokens += int(response.metadata['total_tokens'])
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
        # return await self.retrive_service.process(
        #     RetriveInput(
        #         query=step,
        #     ),
        # )
        return await self.web_search_service.process(
            WebSearchingInput(
                query=step,
                top_k=self.settings.retrive.top_k,
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
            vector_db_output = await self.handle_retriver(step=step)
            for context in vector_db_output.context:
                contexts.append({'content': context})

        else:
            logger.error(f'Unsupported tool selected: {tool}')
            raise ValueError(f'Unsupported tool: {tool}')

        return contexts

    async def validate_output(self, step: str, info: str) -> Dict[str, Any]:
        """Validate the quality of the retrieved information against the query.

        Args:
            step: The original query/step
            info: The retrieved information

        Returns:
            Dictionary with validation results, including if information is sufficient
            and a reformulated query if needed
        """
        messages = [
            CompletionMessage(
                role=MessageRole.SYSTEM,
                content=VALIDATE_OUTPUT_SYSTEM_PROMPT,
            ),
            CompletionMessage(
                role=MessageRole.USER,
                content=VALIDATE_OUTPUT_USER_PROMPT.format(step=step, info=info),
            ),
        ]

        response = await self.llm_service.process(
            LLMBaseInput(messages=messages),
        )

        self.prompt_tokens += int(response.metadata['prompt_tokens'])
        self.completion_tokens += int(response.metadata['completion_tokens'])
        self.total_tokens += int(response.metadata['total_tokens'])

        validation_result_str = response.response.strip()

        try:
            validation_result = json.loads(validation_result_str)
            logger.info(f'Validation result: {validation_result}')
            return validation_result
        except json.JSONDecodeError:
            logger.warning(
                f'Failed to parse validation result as JSON: {validation_result_str}',
            )
            return {
                'is_sufficient': True,
                'reasoning': 'Failed to parse validation result',
                'reformulated_query': step,
            }

    async def process(self, inputs: SubAgentInput) -> SubAgentOutput:
        """Process a step using the appropriate tool and generate a consolidated response.
        If the initial results are inadequate, retry with a reformulated query.

        Args:
            inputs: The SubAgentInput containing the step to process

        Returns:
            SubAgentOutput with consolidated information and metadata
        """
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

        max_retries = 2  # Maximum number of retry attempts
        retry_count = 0
        current_step = inputs.step
        validation_history = []
        all_contexts = []

        try:
            while retry_count <= max_retries:
                contexts = []

                tool = await self.decide_tool(current_step)

                contexts = await self.handle_tool(tool=tool, step=current_step)

                context_dicts = []
                for context in contexts:
                    if isinstance(context, dict):
                        context_dicts.append(context)
                    else:
                        context_dict = {
                            'title': context.title,
                            'url': context.url,
                            'chunks': context.chunks,
                        }
                        context_dicts.append(context_dict)

                # Rerank the contexts
                rerank_output = await self.rerank_service.process(
                    RerankInput(query=current_step, hits=context_dicts),
                )
                contexts = rerank_output.ranked_contexts[: self.settings.retrive.top_k]

                # Clean the context
                cleaned_context = await self.clean_context(
                    step=current_step,
                    context=str(contexts),
                )

                # If this isn't the first attempt, combine with previous relevant contexts
                if retry_count > 0 and all_contexts:
                    combined_contexts = f'Previously retrieved: {all_contexts}\n\nNew retrieval: {cleaned_context}'
                    cleaned_context = await self.clean_context(
                        step=inputs.step,  # Use original query for final cleaning
                        context=combined_contexts,
                    )

                # Store retrieved context for possible future use
                all_contexts = cleaned_context

                # Validate the retrieved information
                if retry_count < max_retries:  # Skip validation on the last attempt
                    validation_result = await self.validate_output(
                        step=inputs.step,  # Always validate against original query
                        info=cleaned_context,
                    )

                    validation_entry = {
                        'attempt': retry_count + 1,
                        'query': current_step,
                        'is_sufficient': validation_result.get('is_sufficient', True),
                        'reasoning': validation_result.get('reasoning', ''),
                    }
                    validation_history.append(validation_entry)

                    # If the information is sufficient, return the result
                    if validation_result.get('is_sufficient', True):
                        logger.info(
                            f'Information deemed sufficient after {retry_count} retries',
                        )
                        break

                    # Otherwise, update the query and retry
                    reformulated_query = validation_result.get(
                        'reformulated_query', current_step,
                    )
                    if reformulated_query == current_step:
                        # If the query wasn't reformulated, add specificity to avoid duplicate search
                        reformulated_query = (
                            f'{current_step} (seeking more specific information)'
                        )

                    current_step = reformulated_query
                    retry_count += 1
                    logger.info(f'Retrying with reformulated query: {current_step}')
                else:
                    break

            metadata = {
                'prompt_tokens': str(self.prompt_tokens),
                'completion_tokens': str(self.completion_tokens),
                'total_tokens': str(self.total_tokens),
                'retry_count': str(retry_count),
                'validation_history': str(validation_history),
            }

            return SubAgentOutput(
                info=all_contexts,
                metadata=metadata,
            )

        except Exception as e:
            logger.exception(
                f'Error in sub-agent processing: {e}',
                extra={
                    'inputs': inputs,
                    'retry_count': retry_count,
                },
            )
            return SubAgentOutput(
                info=f'Error processing request: {str(e)}',
                metadata={
                    'prompt_tokens': str(self.prompt_tokens),
                    'completion_tokens': str(self.completion_tokens),
                    'total_tokens': str(self.total_tokens),
                    'error': str(e),
                },
            )
