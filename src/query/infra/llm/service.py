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

logger = get_logger(__name__)


class LLMInput(BaseModel):
    messages: Message | BatchMessage


class LLMOutput(BaseModel):
    response: Response | BatchResponse
    metadata: dict[str, Any] = {}


class LLMService(LLMBaseService):
    settings: LLMSettings

    @property
    def header(self) -> dict[str, str]:
        """Header for the LLM request"""
        return {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }

    async def inference(
        self,
        messages: Message,
        frequency_penalty: int,
        n: int,
        model: str,
        presence_penalty: int,
        max_completion_tokens: int,
        temperature: float,
    ) -> Response:
        body = {
            'model': model,
            'messages': jsonable_encoder(messages),
            'frequency_penalty': frequency_penalty,
            'n': n,
            'presence_penalty': presence_penalty,
            'max_completion_tokens': max_completion_tokens,
            'temperature': temperature,
        }

        logger.info(f'URL enpoint: {self.settings.url}')

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
        response = await self.inference(
            messages=input.messages,
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
