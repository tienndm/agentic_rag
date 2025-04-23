from __future__ import annotations

import httpx
import numpy as np
from shared.base import AsyncBaseService
from shared.base import BaseModel
from shared.settings import EmbedSettings


class EmbedInput(BaseModel):
    query: list[str]


class EmbedOutput(BaseModel):
    embeddings: list[np.ndarray]


class EmbedService(AsyncBaseService):
    settings: EmbedSettings

    @property
    def header(self) -> dict[str, str]:
        return {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }

    async def process(self, inputs: EmbedInput) -> EmbedOutput:
        body = {
            'query': inputs.query,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                str(self.settings.url),
                headers=self.header,
                json=body,
                timeout=None,
            )

        data = response.json()['info']['data']
        embeddings = [np.array(item['embedding']) for item in data]

        return EmbedOutput(embeddings=embeddings)
