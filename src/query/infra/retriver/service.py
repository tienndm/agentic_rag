from __future__ import annotations

import httpx
from shared.settings import RetriveServiceSettings

from .base import BaseRetriveInput
from .base import BaseRetriveOutput
from .base import BaseRetriveService


class RetriverServiceV1(BaseRetriveService):
    settings: RetriveServiceSettings

    @property
    def header(self) -> dict[str, str]:
        """Header for the LLM request"""
        return {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }

    async def process(self, input: BaseRetriveInput) -> BaseRetriveOutput:
        body = {
            'query': input.query,
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

        return BaseRetriveOutput(
            answer=response.json()['info']['answer'],
            metadata=response.json()['info']['metadata'],
        )
