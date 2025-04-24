from __future__ import annotations

import time

from domain.processor.chunking import ChunkingInput
from domain.processor.chunking import ChunkingService
from duckduckgo_search import DDGS
from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMBaseService
from infra.llm import MessageRole
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import WebSearchSettings

from .cleaner import CleanerInput
from .cleaner import CleanerService
from .loader import LoaderInput
from .loader import LoaderService
from .prompt.web_search import WEB_SEARCHING_PROMPT

logger = get_logger(__name__)


class WebSearchingInput(BaseModel):
    """
    Input model for web search operations.

    Attributes:
        query: The search query to be executed
        top_k: Maximum number of search results to retrieve
    """

    query: str
    top_k: int


class SearchResult(BaseModel):
    """
    Model representing a search result with its content.

    Attributes:
        title: The title of the search result
        url: The URL of the search result
        chunks: Processed text chunks extracted from the search result
    """

    title: str
    url: str
    chunks: list[str]


class WebSearchingOutput(BaseModel):
    """
    Output model for web search operations.

    Attributes:
        contexts: List of search results with their processed content
        metadata: Optional metadata about the search process
    """

    contexts: list[SearchResult]
    metadata: dict[str, str] | None = None


class WebSearchService(BaseService):
    """
    Service for performing web searches and processing the results.

    This service implements a comprehensive web search workflow:
    1. Query optimization using LLM
    2. Web search execution using DuckDuckGo
    3. Content fetching with headless browser
    4. HTML cleaning and text extraction
    5. Content chunking for better processing

    The service includes error handling, retry logic, and graceful degradation
    to ensure robustness when dealing with external web resources.
    """

    llm_service: LLMBaseService
    chunking_service: ChunkingService
    settings: WebSearchSettings

    @property
    def loader(self) -> LoaderService:
        """Returns a service for loading web pages using a headless browser."""
        return LoaderService(settings=self.settings)

    @property
    def cleaner(self) -> CleanerService:
        """Returns a service for cleaning HTML content and extracting relevant text."""
        return CleanerService(settings=self.settings)

    async def fetch_pages(self, urls: list[str]) -> list:
        """
        Fetch and transform HTML content from multiple URLs.

        This method orchestrates a full content processing pipeline:
        1. Fetch HTML content from URLs
        2. Clean the HTML to extract relevant text
        3. Chunk the text for better semantic processing

        Args:
            urls: List of URLs to fetch content from

        Returns:
            List containing cleaned and chunked text from each page
        """
        try:
            html = await self.loader.process(LoaderInput(urls=urls))
            docs = []
            for h in html.contents:
                try:
                    if not isinstance(h, str):
                        h = str(h)

                    cleaned_output = self.cleaner.process(CleanerInput(html=h))

                    if (
                        not cleaned_output.cleaned_text
                        or cleaned_output.cleaned_text.isspace()
                    ):
                        logger.warning(f'Empty cleaned text for URL: {h}')
                        docs.append([])
                        continue

                    chunking_out = await self.chunking_service.process(
                        ChunkingInput(context=cleaned_output.cleaned_text),
                    )

                    if not chunking_out.chunks:
                        logger.warning('No chunks generated for content')
                        docs.append([])
                    else:
                        docs.append(chunking_out.chunks)

                except IndexError as e:
                    logger.error(f'Index error processing HTML: {str(e)}')
                    docs.append([])
                except Exception as e:
                    logger.error(f'Error processing HTML: {str(e)}')
                    docs.append([])
            return docs
        except Exception as e:
            logger.error(f'Error in fetch_pages: {str(e)}')
            return [[f'[Error fetching pages: {str(e)}]']]

    async def pre_process_query(self, query: str) -> str:
        """
        Process the user query through an LLM to optimize for web search.

        Transforms the original query into a form that's more likely to
        produce relevant search results from search engines.

        Args:
            query: User's original search query

        Returns:
            Optimized search query for better web search results
        """
        messages = [
            CompletionMessage(
                role=MessageRole.SYSTEM,
                content=WEB_SEARCHING_PROMPT,
            ),
            CompletionMessage(
                role=MessageRole.USER,
                content=query,
            ),
        ]

        response = await self.llm_service.process(LLMBaseInput(messages=messages))
        return response.response.strip()

    async def process(self, inputs: WebSearchingInput) -> WebSearchingOutput:
        """
        Perform a web search for the given query, fetch results, and process text.

        Implements a complete web search workflow with retry mechanisms and
        error handling to ensure robust operation even with external dependencies.

        The process includes:
        1. Query optimization
        2. Web search with retries
        3. Content fetching and processing
        4. Result consolidation

        Args:
            inputs: WebSearchingInput containing query and top_k parameters

        Returns:
            WebSearchingOutput: Container with processed search results and metadata
        """
        try:
            max_tries = 3
            retry_delay = 3
            results = []

            for attempt in range(max_tries):
                try:
                    processed_query = await self.pre_process_query(inputs.query)
                    results = list(
                        DDGS().text(
                            processed_query,
                            max_results=inputs.top_k,
                        ),
                    )

                    if results:
                        logger.info(f'DDGS search successful on attempt {attempt + 1}')
                        break

                    logger.warning(
                        f'DDGS search returned no results on attempt {attempt + 1}',
                    )
                    if attempt < max_tries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # Exponential backoff
                except Exception as e:
                    logger.error(
                        f'DDGS search error on attempt {attempt + 1}: {str(e)}',
                    )
                    if attempt < max_tries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # Exponential backoff

            if not results:
                logger.error('All DDGS search attempts failed')
                return WebSearchingOutput(
                    contexts=[],
                    metadata={
                        'error': 'Search returned no results after multiple attempts',
                    },
                )

            search_results = []
            urls = []
            for res in results:
                search_results.append(
                    SearchResult(title=res['title'], url=res['href'], chunks=[]),
                )
                urls.append(res['href'])

            docs = await self.fetch_pages(urls)

            final_results = []
            for idx, doc in enumerate(docs):
                if idx < len(search_results):
                    final_results.append(
                        SearchResult(
                            title=search_results[idx].title,
                            url=search_results[idx].url,
                            chunks=doc,
                        ),
                    )

            return WebSearchingOutput(
                contexts=final_results,
                metadata=None,
            )
        except Exception as e:
            logger.error(f'Error in web search process: {str(e)}')
            return WebSearchingOutput(
                contexts=[],
                metadata={'error': f'Web search process failed: {str(e)}'},
            )
