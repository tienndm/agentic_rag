from __future__ import annotations

import re

from bs4 import BeautifulSoup
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import WebSearchSettings

logger = get_logger(__name__)


class CleanerInput(BaseModel):
    html: str


class CleanerOutput(BaseModel):
    cleaned_text: str
    is_captcha: bool = False


class CleanerService(BaseService):
    settings: WebSearchSettings

    def cleanText(self, text: str) -> str:
        """
        Clean text by normalizing whitespace and removing extra characters.

        Args:
            text (str): Raw text to clean.

        Returns:
            str: Cleaned text.
        """
        text = re.sub(r'\s+', ' ', text.strip())
        return re.sub(r'[\r\n\t]+', ' ', text)

    def detect_captcha(self, html: str) -> bool:
        """
        Detect if the HTML contains a Google captcha page.

        Args:
            html (str): HTML content to check

        Returns:
            bool: True if captcha page detected, False otherwise
        """
        captcha_patterns = [
            'Our systems have detected unusual traffic',
            'Please try your request again later',
            'This page appears when Google automatically detects requests',
            'Why did this happen?',
            'Terms of Service',
            'IP address:',
        ]

        pattern_matches = sum(1 for pattern in captcha_patterns if pattern in html)
        return pattern_matches >= 3

    def process(self, inputs: CleanerInput) -> CleanerOutput:
        """
        Extract and clean text from provided HTML content.

        Args:
            inputs (CleanerInput): HTML content to process.

        Returns:
            CleanerOutput: Extracted and cleaned text.
        """
        try:
            if inputs.html.startswith('Error fetching'):
                logger.warning(f'Received error as HTML: {inputs.html}')
                return CleanerOutput(
                    cleaned_text=f'[Failed to fetch content: {inputs.html}]',
                )

            if self.detect_captcha(inputs.html):
                logger.warning('Google captcha page detected')
                return CleanerOutput(
                    cleaned_text='[Google captcha detected - unable to retrieve search results]',
                    is_captcha=True,
                )

            soup = BeautifulSoup(inputs.html, 'html.parser')
            for tag in self.settings.exclude_tags:
                for elem in soup.find_all(tag):
                    elem.decompose()

            for tag in self.settings.exclude_classes:
                for elem in soup.find_all(class_=tag):
                    elem.decompose()

            extractedText = []
            for tag in self.settings.target_tags:
                for elem in soup.find_all(tag):
                    cleanedText = self.cleanText(elem.text)
                    if cleanedText:
                        extractedText.append(cleanedText)

            return CleanerOutput(cleaned_text='\n'.join(extractedText))
        except Exception as e:
            logger.error(f'Error cleaning HTML: {str(e)}')
            return CleanerOutput(cleaned_text=f'[Failed to clean content: {str(e)}]')
