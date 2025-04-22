from __future__ import annotations

import re

from duckduckgo_search import DDGS
from shared.base import BaseModel
from shared.base import BaseService
from shared.settings import WebSearchSettings

from .cleaner import CleanerInput
from .cleaner import CleanerService
from .loader import LoaderInput
from .loader import LoaderService


class WebSearchingInput(BaseModel):
    query: str
    top_k: int


class SearchResult(BaseModel):
    title: str
    url: str
    content: str


class WebSearchingOutput(BaseModel):
    contexts: list[SearchResult]
    metadata: dict[str, str] | None = None


class WebSearchService(BaseService):
    settings: WebSearchSettings

    @property
    def loader(self) -> LoaderService:
        return LoaderService(settings=self.settings)

    @property
    def cleaner(self) -> CleanerService:
        return CleanerService(settings=self.settings)

    async def getPage(self, urls: list[str]) -> list[str]:
        """
        Fetch and transform HTML content from multiple URLs.

        Args:
            urls (list): List of URLs to fetch.

        Returns:
            list: List containing cleaned text from each page.
        """
        html = await self.loader.process(
            LoaderInput(
                urls=urls,
            ),
        )
        docs = []
        for h in html:
            doc = self.cleaner.process(CleanerInput(html=h))
            docs.append(doc)
        return docs

    def truncate(self, text: str, length: int = 1024) -> str:
        """
        Truncate text to a specified number of words.

        Args:
            text (str): The text to truncate.
            length (int): Maximum number of words to keep.

        Returns:
            str: Truncated text.
        """
        words = text.split()
        return ' '.join(words[:length])

    async def process(self, inputs: WebSearchingInput) -> WebSearchingOutput:
        """
        Perform a web search for the given query, fetch results, and return aggregated text.

        Args:
            query (str): Search query.
            numRes (int): Number of search results to retrieve.

        Returns:
            WebSearchingOutput: Container with search results and metadata.
        """
        results = DDGS().text(inputs.query, max_results=inputs.top_k)
        search_results = []
        urls = []
        for res in results:
            search_results.append(
                SearchResult(title=res['title'], url=res['href'], content=''),
            )
            urls.append(res['href'])
        docs = await self.getPage(urls)

        final_results = []
        for idx, doc in enumerate(docs):
            if idx < len(search_results):
                cleaned_text = re.sub(r'\n+', '\n', doc).strip()
                final_results.append(
                    SearchResult(
                        title=search_results[idx].title,
                        url=search_results[idx].url,
                        content=cleaned_text,
                    ),
                )

        return WebSearchingOutput(
            contexts=final_results,
            metadata=None,
        )
