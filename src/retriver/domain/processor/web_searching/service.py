from __future__ import annotations

import asyncio
from typing import List
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMBaseService
from infra.llm import MessageRole
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import LLMSettings

from .prompt.web_search import WEB_SEARCHING_PROMPT


logger = get_logger(__name__)


class WebSearchingInput(BaseModel):
    query: str
    context: Optional[str] = None
    fetch_content: bool = False


class WebSearchingOutput(BaseModel):
    answer: str
    metadata: dict[str, str] | None = None
    sources: list[str]


class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    full_content: Optional[str] = None


class WebSearchingService(BaseService):
    llm_model: LLMBaseService
    settings: LLMSettings

    async def process(self, input: WebSearchingInput) -> WebSearchingOutput:
        """
        Process a web search query and provide relevant information.

        Args:
            input: WebSearchingInput containing the search query and context

        Returns:
            WebSearchingOutput with the answer and token count
        """
        search_results = await self._search_duckduckgo(input.query)

        if not search_results:
            logger.warning('No search results found')
            return WebSearchingOutput(
                answer='No results found for the given query.', num_tokens=0, sources=[],
            )

        if input.fetch_content:
            await self._fetch_and_parse_urls(search_results)

        search_context = self._create_search_context(search_results, input.context)

        message = self._create_llm_prompt(input.query, search_context)

        llm_response = await self.llm_model.process(LLMBaseInput(messages=message))

        sources = [
            {'title': result.title, 'url': result.url} for result in search_results
        ]

        return WebSearchingOutput(
            answer=llm_response.response,
            metadata=llm_response.metadata,
            sources=sources,
        )

    async def _search_duckduckgo(
        self, query: str, max_results: int = 5,
    ) -> List[SearchResult]:
        """
        Search DuckDuckGo for the given query.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of SearchResult objects
        """
        results = []

        # Run in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        raw_results = await loop.run_in_executor(
            None, lambda: list(DDGS().text(query, max_results=max_results)),
        )

        for result in raw_results:
            title = result.get('title', '')
            url = result.get('href', '')
            snippet = result.get('body', '')

            results.append(SearchResult(title=title, url=url, content=snippet))

        return results

    async def _fetch_and_parse_urls(
        self, search_results: List[SearchResult], timeout: int = 10,
    ) -> None:
        """
        Fetch the content of each URL and extract relevant text.

        Args:
            search_results: List of SearchResult objects to update with full content
            timeout: Timeout in seconds for each HTTP request
        """

        async def fetch_url(session, result):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                }
                async with session.get(
                    result.url, headers=headers, timeout=timeout,
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        result.full_content = self._extract_main_content(html)
                    else:
                        logger.warning(
                            f'Failed to fetch URL {result.url}, status code: {response.status}',
                        )
            except Exception as e:
                logger.error(f'Error fetching URL {result.url}: {str(e)}')

        async with aiohttp.ClientSession() as session:
            tasks = [fetch_url(session, result) for result in search_results]
            await asyncio.gather(*tasks)

    def _extract_main_content(self, html_content: str, max_length: int = 8000) -> str:
        """
        Extract the main content from an HTML page.

        Args:
            html_content: Raw HTML content
            max_length: Maximum length of content to return

        Returns:
            Extracted text content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script_or_style in soup(['script', 'style', 'header', 'footer', 'nav']):
                script_or_style.extract()

            # Extract text from body
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split('  '))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            # Truncate if needed
            if len(text) > max_length:
                text = text[:max_length] + '...'

            return text
        except Exception as e:
            logger.error(f'Error extracting content: {str(e)}')
            return ''

    def _create_search_context(
        self, search_results: List[SearchResult], user_context: str,
    ) -> str:
        """
        Create a formatted context string from search results.

        Args:
            search_results: List of SearchResult objects
            user_context: Original context from the user

        Returns:
            Formatted context string for the LLM
        """
        context_parts = []

        # Only include user context if it's not empty
        if user_context:
            context_parts.append(f'User Context: {user_context}\n')

        context_parts.append('Search Results:')

        for i, result in enumerate(search_results, 1):
            context_parts.append(f'{i}. Title: {result.title}')
            context_parts.append(f'   URL: {result.url}')

            # Use full content if available, otherwise use snippet
            content = result.full_content if result.full_content else result.content

            # Truncate content if it's too long
            if len(content) > 1000:
                content = content[:1000] + '...'

            context_parts.append(f'   Content: {content}')
            context_parts.append('')

        return '\n'.join(context_parts)

    def _create_llm_prompt(self, query: str, search_context: str) -> str:
        """
        Create a prompt for the LLM to generate an answer based on search results.

        Args:
            query: The original query
            search_context: Formatted context from search results

        Returns:
            Complete prompt for the LLM
        """
        message = [
            CompletionMessage(
                role=MessageRole.USER,
                content=WEB_SEARCHING_PROMPT.format(
                    query=query, search_context=search_context,
                ),
            ),
        ]

        return message
