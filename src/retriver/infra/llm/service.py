from __future__ import annotations

from typing import Any

import httpx
from fastapi.encoders import jsonable_encoder
from shared.base import BaseModel
from shared.logging import get_logger
from shared.settings import LLMSettings

from .base import LLMBaseService
from .datatypes import BatchMessage
from .datatypes import BatchResponse
from .datatypes import Message
from .datatypes import Response
"""
LLM Service Module

This module provides functionality to interact with external language models
through an API interface, handling message formatting, request processing,
and response parsing.
"""

logger = get_logger(__name__)


class LLMInput(BaseModel):
    """
    Input model for the LLM service.

    Attributes:
        messages (Message | BatchMessage): Single message or batch of messages to send to the LLM.
    """

    messages: Message | BatchMessage


class LLMOutput(BaseModel):
    """
    Output model for the LLM service.

    Attributes:
        response (Response | BatchResponse): The response text from the LLM.
        metadata (dict[str, Any]): Additional metadata about the response, like token counts.
    """

    response: Response | BatchResponse
    metadata: dict[str, Any] = {}


class LLMService(LLMBaseService):
    """
    Service responsible for interacting with language model APIs.

    This service handles the communication with external language model services,
    including request formatting, error handling, and response processing.
    It manages all aspects of LLM inference needed by the application.

    Attributes:
        settings (LLMSettings): Configuration settings for the LLM service.
    """

    settings: LLMSettings

    @property
    def header(self) -> dict[str, str]:
        """
        HTTP headers for LLM API requests.

        Returns:
            dict[str, str]: Dictionary of HTTP headers for the LLM API requests.
        """
        return {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }

    async def inference(
        self,
        message: Message,
        frequency_penalty: int,
        n: int,
        model: str,
        presence_penalty: int,
        max_completion_tokens: int,
        temperature: float,
    ) -> Response:
        """
        Make an inference request to the LLM API.

        Args:
            message (Message): The message to send to the LLM.
            frequency_penalty (int): Penalty for using frequent tokens.
            n (int): Number of completions to generate.
            model (str): Name of the LLM model to use.
            presence_penalty (int): Penalty for repeating tokens.
            max_completion_tokens (int): Maximum number of tokens to generate.
            temperature (float): Sampling temperature for generation.

        Returns:
            Response: The LLM response with content and token usage statistics.

        Raises:
            Exception: If the LLM request fails or returns an error.
        """
        body = {
            'model': model,
            'messages': jsonable_encoder(message),
            'frequency_penalty': frequency_penalty,
            'n': n,
            'presence_penalty': presence_penalty,
            'max_completion_tokens': max_completion_tokens,
            'temperature': temperature,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                str(self.settings.url),
                headers=self.header,
                json=body,
                timeout=None,
            )
        if response.status_code != 200:
            raise Exception(
                f'LLM request failed with status code {response.status_code}: {response.text}',
            )
        return {
            'message': response.json()['choices'][0]['message']['content'],
            'prompt_tokens': response.json()['usage']['prompt_tokens'],
            'completion_tokens': response.json()['usage']['completion_tokens'],
            'total_tokens': response.json()['usage']['total_tokens'],
        }

    async def process(self, input: LLMInput) -> LLMOutput:
        """
        Process an LLM request and return the response.

        This method handles the high-level workflow of sending a request to the LLM
        and formatting the response for use by the application.

        Args:
            input (LLMInput): The input containing messages for the LLM.

        Returns:
            LLMOutput: The LLM's response text and associated metadata.

        Raises:
            Exception: If there's an error during the API request or response processing.
        """
        response = await self.inference(
            message=input.messages,
            frequency_penalty=self.settings.frequency_penalty,
            n=self.settings.n,
            model=self.settings.model,
            presence_penalty=self.settings.presence_penalty,
            max_completion_tokens=self.settings.max_completion_tokens,
            temperature=self.settings.temperature,
        )
        return LLMOutput(
            response=response['message'],
            metadata={
                'prompt_tokens': str(response['prompt_tokens']),
                'completion_tokens': str(response['completion_tokens']),
                'total_tokens': str(response['total_tokens']),
            },
        )
