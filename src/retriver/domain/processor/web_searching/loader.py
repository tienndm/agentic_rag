from __future__ import annotations

import asyncio

from playwright.async_api import async_playwright
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import WebSearchSettings

logger = get_logger(__name__)


class LoaderInput(BaseModel):
    urls: list[str]


class LoaderOutput(BaseModel):
    contents: list[str]


class LoaderService(BaseService):
    settings: WebSearchSettings

    async def fetch(self, url: str) -> str:
        """
        Fetch the HTML content from a specified URL.

        Args:
            url (str): The URL to fetch.

        Returns:
            str: The HTML content of the page or an exception if error occurs.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.settings.headless)
            page = await browser.new_page()
            try:
                logger.debug(f'#web_searcher - fetch - url: {url}')
                await page.goto(url, timeout=self.settings.timeout)
                content = await page.content()
                return content
            except Exception as e:
                return e
            finally:
                await browser.close()

    async def process(self, inputs: LoaderInput) -> LoaderOutput:
        """
        Fetch HTML content from multiple URLs concurrently.

        Args:
            urls (list): List of URLs to fetch.

        Returns:
            list: List of HTML contents for each URL.
        """
        tasks = [self.fetch(url) for url in inputs.urls]
        return await asyncio.gather(*tasks)
