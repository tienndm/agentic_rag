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
                return CleanerOutput(cleaned_text=f'[Failed to fetch content: {inputs.html}]')

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
