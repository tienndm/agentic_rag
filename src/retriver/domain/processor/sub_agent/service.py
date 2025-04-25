from __future__ import annotations

import uuid
from typing import Dict
from typing import Optional

from domain.processor.rerank import RerankService
from domain.processor.retrive import RetriveService
from domain.processor.web_searching import WebSearchService
from infra.llm import LLMService
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import Settings

from .context_cleaner import ContextCleanerHandler
from .memory import MemoryManager
from .memory import MemoryManagerInput
from .output_validator import OutputValidatorHandler
from .tool_decision import ToolDecisionHandler
from .tool_handler import ToolOperationHandler

logger = get_logger(__name__)


class SubAgentInput(BaseModel):
    """
    Input model for the SubAgent service.

    Attributes:
        step: A specific information retrieval step or query to be processed
        query_id: Optional unique identifier for the query/conversation
    """

    step: str
    query_id: str = ''


class SubAgentOutput(BaseModel):
    """
    Output model for the SubAgent service.

    Attributes:
        info: The processed and consolidated information retrieved
        metadata: Optional processing metadata including token counts and validation history
        query_id: The ID of the processed query for future reference
    """

    info: str
    metadata: Dict[str, str] | None = None
    query_id: str = ''


class SubAgentService(BaseService):
    """
    Service for handling contextual information retrieval using dynamic tool selection.

    SubAgentService functions as an intelligent router that:
    1. Analyzes the information need specified in a query
    2. Selects the optimal retrieval mechanism (web search or vector DB)
    3. Cleans and processes retrieved contexts
    4. Validates information quality and sufficiency
    5. Reformulates queries when needed to fill information gaps

    The service implements a self-improving feedback loop where insufficient results
    trigger query reformulation and additional retrieval attempts.
    """

    settings: Optional[Settings] = None
    llm_service: Optional[LLMService] = None
    web_search_service: Optional[WebSearchService] = None
    retrive_service: Optional[RetriveService] = None
    rerank_service: Optional[RerankService] = None
    _memory_manager: Optional[MemoryManager] = None

    def __init__(
        self,
        settings: Optional[Settings] = None,
        llm_service: Optional[LLMService] = None,
        web_search_service: Optional[WebSearchService] = None,
        retrive_service: Optional[RetriveService] = None,
        rerank_service: Optional[RerankService] = None,
    ):
        """
        Initialize the SubAgentService with the specified services.

        For testing purposes, services can be None. In production, all services should be provided.

        Args:
            settings: Application settings
            llm_service: Service for language model operations
            web_search_service: Service for web searching
            retrive_service: Service for retrieving information from vector database
            rerank_service: Service for reranking search results
        """
        super().__init__()

        self.settings = settings
        self.llm_service = llm_service
        self.web_search_service = web_search_service
        self.retrive_service = retrive_service
        self.rerank_service = rerank_service

        if llm_service is not None:
            self._memory_manager = MemoryManager(llm_service=self.llm_service)

    @property
    def tool_decision_handler(self) -> ToolDecisionHandler:
        """Get the tool decision handler instance."""
        if self.llm_service is None:
            raise ValueError('LLMService not initialized')
        return ToolDecisionHandler(llm_service=self.llm_service)

    @property
    def context_cleaner_handler(self) -> ContextCleanerHandler:
        """Get the context cleaner handler instance."""
        if self.llm_service is None:
            raise ValueError('LLMService not initialized')
        return ContextCleanerHandler(llm_service=self.llm_service)

    @property
    def output_validator_handler(self) -> OutputValidatorHandler:
        """Get the output validator handler instance."""
        if self.llm_service is None:
            raise ValueError('LLMService not initialized')
        return OutputValidatorHandler(llm_service=self.llm_service)

    @property
    def tool_operation_handler(self) -> ToolOperationHandler:
        """Get the tool operation handler instance."""
        if (
            self.settings is None
            or self.web_search_service is None
            or self.retrive_service is None
            or self.rerank_service is None
        ):
            raise ValueError('Required services not initialized')
        return ToolOperationHandler(
            settings=self.settings.retrive,
            web_search_service=self.web_search_service,
            retrive_service=self.retrive_service,
            rerank_service=self.rerank_service,
        )

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    async def process(self, inputs: SubAgentInput) -> SubAgentOutput:
        """
        Process a step using the appropriate tool and generate a consolidated response.

        Implements an adaptive information retrieval workflow that:
        1. Selects the optimal tool for the information need
        2. Retrieves and processes information
        3. Validates information quality
        4. Reformulates queries and retries if needed
        5. Maintains a memory of retrieved information to optimize searches

        The process is self-correcting, aiming to maximize information quality
        through iterative refinement when needed.

        Args:
            inputs: The SubAgentInput containing the step to process

        Returns:
            SubAgentOutput: Consolidated information and processing metadata
        """
        if (
            self.settings is None
            or self.llm_service is None
            or self.web_search_service is None
            or self.retrive_service is None
            or self.rerank_service is None
            or self._memory_manager is None
        ):
            return SubAgentOutput(
                info=f'This is a test response for query: {inputs.step}',
                metadata={'note': 'Test mode - services not initialized'},
                query_id=inputs.query_id if inputs.query_id else str(uuid.uuid4()),
            )

        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

        query_id = inputs.query_id if inputs.query_id else str(uuid.uuid4())

        max_retries = 3
        retry_count = 0
        current_step = inputs.step
        validation_history = []

        try:
            while retry_count <= max_retries:
                tool = await self.tool_decision_handler.process(current_step)
                self.prompt_tokens += self.tool_decision_handler.prompt_tokens
                self.completion_tokens += self.tool_decision_handler.completion_tokens
                self.total_tokens += self.tool_decision_handler.total_tokens

                get_cache_input = MemoryManagerInput(
                    query_id=query_id,
                    action='get_cache',
                    step=current_step,
                )
                cache_result = await self._memory_manager.process(get_cache_input)
                cached_context = cache_result.result

                if cached_context:
                    logger.info(f'Using cached context for step: {current_step}')
                    contexts = cached_context
                    search_failed = False
                else:
                    contexts, search_failed = await self.tool_operation_handler.process(
                        tool=tool,
                        step=current_step,
                    )

                    if not search_failed and contexts:
                        cache_input = MemoryManagerInput(
                            query_id=query_id,
                            action='cache',
                            step=current_step,
                            context=str(contexts),
                        )
                        await self._memory_manager.process(cache_input)

                if search_failed:
                    retry_count += 1

                    if retry_count <= max_retries:
                        current_step = (
                            f'{current_step} (alternative information {retry_count})'
                        )
                        logger.info(
                            f'Retrying immediately with modified query: {current_step}',
                        )
                        continue
                    else:
                        logger.warning(
                            'Max retries reached with search failures, proceeding with available data',
                        )

                if not search_failed and contexts:
                    if isinstance(contexts, str):
                        try:
                            import ast

                            contexts = ast.literal_eval(contexts)
                        except (ValueError, SyntaxError):
                            contexts = [
                                {
                                    'content': contexts,
                                    'title': 'Cached Content',
                                    'url': '',
                                },
                            ]

                    contexts = await self.tool_operation_handler.rerank_contexts(
                        current_step,
                        contexts,
                    )

                cleaned_context = await self.context_cleaner_handler.process(
                    step=current_step,
                    context=str(contexts),
                )
                self.prompt_tokens += self.context_cleaner_handler.prompt_tokens
                self.completion_tokens += self.context_cleaner_handler.completion_tokens
                self.total_tokens += self.context_cleaner_handler.total_tokens

                merge_input = MemoryManagerInput(
                    query_id=query_id,
                    action='merge',
                    query=inputs.step,
                    context=cleaned_context,
                )
                merge_result = await self._memory_manager.process(merge_input)
                merged_context = merge_result.result

                self.prompt_tokens += int(merge_result.metadata.get('prompt_tokens', 0))
                self.completion_tokens += int(
                    merge_result.metadata.get('completion_tokens', 0),
                )
                self.total_tokens += int(merge_result.metadata.get('total_tokens', 0))

                if retry_count < max_retries:
                    validation_result = await self.output_validator_handler.process(
                        step=inputs.step,
                        info=merged_context,
                    )
                    self.prompt_tokens += self.output_validator_handler.prompt_tokens
                    self.completion_tokens += (
                        self.output_validator_handler.completion_tokens
                    )
                    self.total_tokens += self.output_validator_handler.total_tokens

                    validation_entry = {
                        'attempt': retry_count + 1,
                        'query': current_step,
                        'is_sufficient': validation_result.get('is_sufficient', True),
                        'reasoning': validation_result.get('reasoning', ''),
                    }
                    validation_history.append(validation_entry)

                    if validation_result.get('is_sufficient', True):
                        logger.info(
                            f'Information deemed sufficient after {retry_count} retries',
                        )
                        break

                    reformulated_query = validation_result.get(
                        'reformulated_query',
                        current_step,
                    )

                    if 'missing_aspects' in validation_result:
                        missing_aspects = validation_result.get('missing_aspects', [])
                        update_input = MemoryManagerInput(
                            query_id=query_id,
                            action='update',
                            missing_aspects=missing_aspects,
                        )
                        await self._memory_manager.process(update_input)

                    if reformulated_query != current_step:
                        current_step = reformulated_query
                    else:
                        get_input = MemoryManagerInput(query_id=query_id, action='get')
                        memory_result = await self._memory_manager.process(get_input)
                        missing_aspects = memory_result.metadata.get(
                            'missing_aspects',
                            [],
                        )

                        if missing_aspects:
                            missing_info = ', '.join(missing_aspects)
                            current_step = f'Regarding {inputs.step}, specifically find information about: {missing_info}'
                        else:
                            current_step = (
                                f'{inputs.step} (need more comprehensive information)'
                            )

                    retry_count += 1
                    logger.info(
                        f'Retrying with targeted query for missing info: {current_step}',
                    )
                else:
                    break

            get_input = MemoryManagerInput(query_id=query_id, action='get')
            memory_result = await self._memory_manager.process(get_input)
            final_info = memory_result.result
            missing_aspects = memory_result.metadata.get('missing_aspects', [])

            metadata = {
                'prompt_tokens': str(self.prompt_tokens),
                'completion_tokens': str(self.completion_tokens),
                'total_tokens': str(self.total_tokens),
                'retry_count': str(retry_count),
                'validation_history': str(validation_history),
                'missing_aspects': str(missing_aspects),
                'query_id': query_id,
            }

            return SubAgentOutput(
                info=final_info,
                metadata=metadata,
                query_id=query_id,
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
                query_id=query_id,
            )
