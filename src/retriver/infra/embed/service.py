from __future__ import annotations

import httpx
import numpy as np
from shared.base import BaseModel
from shared.base import BaseService
from shared.settings import EmbedSettings


class EmbedInput(BaseModel):
    query: list[str]


class EmbedOutput(BaseModel):
    embeddings: list[dict[str, np.ndarray]]


class EmbedService(BaseService):
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

        return EmbedOutput(
            embeddings=response.json()['info']['data'],
        )
