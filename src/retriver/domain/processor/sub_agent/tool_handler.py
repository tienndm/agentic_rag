from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from domain.processor.rerank import RerankInput
from domain.processor.rerank import RerankService
from domain.processor.retrive import RetriveOutput
from domain.processor.retrive import RetriveService
from domain.processor.web_searching import WebSearchingInput
from domain.processor.web_searching import WebSearchingOutput
from domain.processor.web_searching import WebSearchService
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import RetriveSettings

logger = get_logger(__name__)


class ToolOperationHandler(BaseService):
    """
    Handler for performing operations using different retrieval tools.
    """

    settings: RetriveSettings

    web_search_service: WebSearchService
    retrive_service: RetriveService
    rerank_service: RerankService

    async def handle_web_search(self, step: str) -> Tuple[WebSearchingOutput, bool]:
        """
        Handle web search for a given information need.

        Delegates to the WebSearchService to retrieve up-to-date information
        from the internet based on the query.

        Args:
            step: The search query

        Returns:
            Tuple[WebSearchingOutput, bool]: Container with search results and a flag indicating if search failed
        """
        output = await self.web_search_service.process(
            WebSearchingInput(
                query=step,
                top_k=self.settings.top_k,
            ),
        )

        search_failed = False
        if not output.contexts:
            search_failed = True
            logger.warning(f'Web search returned no results for: {step}')
        else:
            empty_or_error_count = 0
            for context in output.contexts:
                if not context.chunks or any(
                    'captcha' in chunk.lower() for chunk in context.chunks
                ):
                    empty_or_error_count += 1

            if empty_or_error_count > len(output.contexts) * 0.5:
                search_failed = True
                logger.warning(
                    f'Web search returned mostly empty or error results for: {step}',
                )

        return output, search_failed

    async def handle_retriver(self, step: str) -> Tuple[RetriveOutput, bool]:
        """
        Handle vector database query for a given information need.

        Note: Currently implemented to use web search as a fallback.

        Args:
            step: The vector database query

        Returns:
            Tuple[RetriveOutput, bool]: Container with retrieved contexts and a flag indicating if search failed
        """
        # return await self.retrive_service.process(
        #     RetriveInput(
        #         query=step,
        #     ),
        # )
        output, search_failed = await self.handle_web_search(step=step)
        return output, search_failed

    async def process(self, tool: str, step: str) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Process a step using the selected retrieval tool.

        Dispatches the query to either web search or vector DB retrieval
        based on the selected tool, and formats the results consistently.

        Args:
            tool: The tool to use ("web_search" or "vector_db")
            step: The processing step/query

        Returns:
            Tuple[List[Dict[str, Any]], bool]: List of context dictionaries and a flag indicating if search failed

        Raises:
            ValueError: If an unsupported tool is specified
        """
        contexts = []
        search_failed = False

        if tool == 'web_search':
            web_search_output, search_failed = await self.handle_web_search(step=step)
            contexts = web_search_output.contexts

        elif tool == 'vector_db':
            vector_db_output, search_failed = await self.handle_retriver(step=step)
            contexts = vector_db_output.contexts
            # for context in vector_db_output.context:
            #     contexts.append({'content': context})

        else:
            logger.error(f'Unsupported tool selected: {tool}')
            raise ValueError(f'Unsupported tool: {tool}')

        return contexts, search_failed

    async def rerank_contexts(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Rerank the contexts based on relevance to the query.

        Args:
            query: The query to rank against
            contexts: The contexts to rerank

        Returns:
            List[Dict[str, Any]]: List of reranked contexts limited by top_k setting
        """
        if not contexts:
            logger.warning('No contexts to rerank, returning empty list')
            return []

        context_dicts = []
        for context in contexts:
            if isinstance(context, dict):
                context_dicts.append(context)
            elif isinstance(context, str):
                # Handle string contexts by wrapping them in a dict
                context_dict = {
                    'content': context,
                    'title': '',
                    'url': '',
                    'chunks': [context],
                }
                context_dicts.append(context_dict)
            else:
                # For object-like contexts with attributes
                try:
                    context_dict = {
                        'title': getattr(context, 'title', ''),
                        'url': getattr(context, 'url', ''),
                        'chunks': getattr(context, 'chunks', []),
                    }
                    context_dicts.append(context_dict)
                except Exception as e:
                    logger.warning(f'Failed to process context: {e}')
                    # Create minimal context dict to avoid failing
                    if hasattr(context, '__str__'):
                        context_dict = {
                            'content': str(context),
                            'chunks': [str(context)],
                        }
                        context_dicts.append(context_dict)

        rerank_output = await self.rerank_service.process(
            RerankInput(query=query, hits=context_dicts),
        )
        return rerank_output.ranked_contexts[: self.settings.top_k]
