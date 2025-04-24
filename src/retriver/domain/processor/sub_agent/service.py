from __future__ import annotations

from typing import Dict

from domain.processor.rerank import RerankService
from domain.processor.retrive import RetriveService
from domain.processor.web_searching import WebSearchService
from infra.llm import LLMService
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import Settings

from .context_cleaner import ContextCleanerHandler
from .output_validator import OutputValidatorHandler
from .tool_decision import ToolDecisionHandler
from .tool_handler import ToolOperationHandler

logger = get_logger(__name__)


class SubAgentInput(BaseModel):
    """
    Input model for the SubAgent service.

    Attributes:
        step: A specific information retrieval step or query to be processed
    """

    step: str


class SubAgentOutput(BaseModel):
    """
    Output model for the SubAgent service.

    Attributes:
        info: The processed and consolidated information retrieved
        metadata: Optional processing metadata including token counts and validation history
    """

    info: str
    metadata: Dict[str, str] | None = None


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

    settings: Settings
    llm_service: LLMService
    web_search_service: WebSearchService
    retrive_service: RetriveService
    rerank_service: RerankService

    @property
    def tool_decision_handler(self) -> ToolDecisionHandler:
        return ToolDecisionHandler(self.llm_service)

    @property
    def context_cleaner_handler(self) -> ContextCleanerHandler:
        return ContextCleanerHandler(self.llm_service)

    @property
    def output_validator_handler(self) -> OutputValidatorHandler:
        return OutputValidatorHandler(self.llm_service)

    @property
    def tool_operation_handler(self) -> ToolOperationHandler:
        return ToolOperationHandler(
            self.settings,
            self.web_search_service,
            self.retrive_service,
            self.rerank_service,
        )

    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    async def process(self, inputs: SubAgentInput) -> SubAgentOutput:
        """
        Process a step using the appropriate tool and generate a consolidated response.

        Implements an adaptive information retrieval workflow that:
        1. Selects the optimal tool for the information need
        2. Retrieves and processes information
        3. Validates information quality
        4. Reformulates queries and retries if needed

        The process is self-correcting, aiming to maximize information quality
        through iterative refinement when needed.

        Args:
            inputs: The SubAgentInput containing the step to process

        Returns:
            SubAgentOutput: Consolidated information and processing metadata
        """
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

        max_retries = 2
        retry_count = 0
        current_step = inputs.step
        validation_history = []
        all_contexts = []

        try:
            while retry_count <= max_retries:
                # Decide which tool to use
                tool = await self.tool_decision_handler.decide_tool(current_step)
                self.prompt_tokens += self.tool_decision_handler.prompt_tokens
                self.completion_tokens += self.tool_decision_handler.completion_tokens
                self.total_tokens += self.tool_decision_handler.total_tokens

                # Handle tool operation and retrieve contexts
                contexts = await self.tool_operation_handler.handle_tool(
                    tool=tool, step=current_step,
                )

                # Rerank the contexts
                contexts = await self.tool_operation_handler.rerank_contexts(
                    current_step, contexts,
                )

                # Clean the context
                cleaned_context = await self.context_cleaner_handler.clean_context(
                    step=current_step,
                    context=str(contexts),
                )
                self.prompt_tokens += self.context_cleaner_handler.prompt_tokens
                self.completion_tokens += self.context_cleaner_handler.completion_tokens
                self.total_tokens += self.context_cleaner_handler.total_tokens

                # If this isn't the first attempt, combine with previous relevant contexts
                if retry_count > 0 and all_contexts:
                    combined_contexts = f'Previously retrieved: {all_contexts}\n\nNew retrieval: {cleaned_context}'
                    cleaned_context = await self.context_cleaner_handler.clean_context(
                        step=inputs.step,
                        context=combined_contexts,
                    )
                    self.prompt_tokens += self.context_cleaner_handler.prompt_tokens
                    self.completion_tokens += (
                        self.context_cleaner_handler.completion_tokens
                    )
                    self.total_tokens += self.context_cleaner_handler.total_tokens

                # Store retrieved context for possible future use
                all_contexts = cleaned_context

                # Validate the retrieved information
                if retry_count < max_retries:
                    validation_result = (
                        await self.output_validator_handler.validate_output(
                            step=inputs.step,
                            info=cleaned_context,
                        )
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

                    # If the information is sufficient, return the result
                    if validation_result.get('is_sufficient', True):
                        logger.info(
                            f'Information deemed sufficient after {retry_count} retries',
                        )
                        break

                    # Otherwise, update the query and retry
                    reformulated_query = validation_result.get(
                        'reformulated_query',
                        current_step,
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
