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
            user_agent = getattr(
                self.settings,
                'user_agent',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            )
            page = await browser.new_page(user_agent=user_agent)
            try:
                await page.goto(url, timeout=self.settings.timeout)
                content = await page.content()
                return content
            except Exception as e:
                logger.exception(f'Error crawling web: {e}')
                return f'Error fetching {url}: {str(e)}'
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
        html = await asyncio.gather(*tasks)
        return LoaderOutput(contents=html)
