from __future__ import annotations

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
from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class ToolOperationHandler:
    """
    Handler for performing operations using different retrieval tools.
    """

    settings: Settings
    web_search_service: WebSearchService
    retrive_service: RetriveService
    rerank_service: RerankService

    async def handle_web_search(self, step: str) -> WebSearchingOutput:
        """
        Handle web search for a given information need.

        Delegates to the WebSearchService to retrieve up-to-date information
        from the internet based on the query.

        Args:
            step: The search query

        Returns:
            WebSearchingOutput: Container with search results and metadata
        """
        return await self.web_search_service.process(
            WebSearchingInput(
                query=step,
                top_k=self.settings.retrive.top_k,
            ),
        )

    async def handle_retriver(self, step: str) -> RetriveOutput:
        """
        Handle vector database query for a given information need.

        Note: Currently implemented to use web search as a fallback.

        Args:
            step: The vector database query

        Returns:
            RetriveOutput: Container with retrieved contexts
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
        """
        Process a step using the selected retrieval tool.

        Dispatches the query to either web search or vector DB retrieval
        based on the selected tool, and formats the results consistently.

        Args:
            tool: The tool to use ("web_search" or "vector_db")
            step: The processing step/query

        Returns:
            List[Dict[str, Any]]: List of context dictionaries

        Raises:
            ValueError: If an unsupported tool is specified
        """
        contexts = []

        if tool == 'web_search':
            web_search_output = await self.handle_web_search(step=step)
            contexts = web_search_output.contexts

        elif tool == 'vector_db':
            vector_db_output = await self.handle_retriver(step=step)
            contexts = vector_db_output.contexts
            # for context in vector_db_output.context:
            #     contexts.append({'content': context})

        else:
            logger.error(f'Unsupported tool selected: {tool}')
            raise ValueError(f'Unsupported tool: {tool}')

        return contexts

    async def rerank_contexts(
        self, query: str, contexts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Rerank the contexts based on relevance to the query.

        Args:
            query: The query to rank against
            contexts: The contexts to rerank

        Returns:
            List[Dict[str, Any]]: List of reranked contexts limited by top_k setting
        """
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
            RerankInput(query=query, hits=context_dicts),
        )
        return rerank_output.ranked_contexts[: self.settings.retrive.top_k]
