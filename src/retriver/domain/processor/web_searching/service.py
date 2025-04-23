from __future__ import annotations

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
    """Input model for web search operations."""

    query: str
    top_k: int


class SearchResult(BaseModel):
    """Model representing a search result with its content."""

    title: str
    url: str
    chunks: list[str]


class WebSearchingOutput(BaseModel):
    """Output model for web search operations."""

    contexts: list[SearchResult]
    metadata: dict[str, str] | None = None


class WebSearchService(BaseService):
    """Service for performing web searches and processing the results."""

    llm_service: LLMBaseService
    chunking_service: ChunkingService
    settings: WebSearchSettings

    @property
    def loader(self) -> LoaderService:
        return LoaderService(settings=self.settings)

    @property
    def cleaner(self) -> CleanerService:
        return CleanerService(settings=self.settings)

    async def fetch_pages(self, urls: list[str]) -> list:
        """
        Fetch and transform HTML content from multiple URLs.

        Args:
            urls: List of URLs to fetch.

        Returns:
            List containing cleaned and chunked text from each page.
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
                        logger.warning('Empty cleaned text for URL')
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

        Args:
            query: User's original search query.

        Returns:
            Optimized search query.
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

        Args:
            inputs: WebSearchingInput containing query and top_k parameters.

        Returns:
            WebSearchingOutput: Container with processed search results and metadata.
        """
        results = DDGS().text(
            await self.pre_process_query(inputs.query),
            max_results=inputs.top_k,
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
