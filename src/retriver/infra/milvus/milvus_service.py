from __future__ import annotations

from typing import Any

import numpy as np
from infra.embed import EmbedInput
from infra.embed import EmbedService
from shared.base import BaseService
from shared.settings import MilvusSettings

from .milvus_driver import MilvusDriver
from .models import MilvusInput
from .models import MilvusOutput


class MilvusService(BaseService):
    settings: MilvusSettings
    embed_service: EmbedService

    @property
    def _driver(self):
        return MilvusDriver(self.settings).driver

    def execute_query(
        self,
        vector: np.ndarray,
        params: dict[str, Any] | None,
        output_format: list[str],
    ):
        result = self._driver.search(
            collection_name=self.settings.collection_name,
            anns_field=self.settings.anns_field,
            data=[vector],
            limit=self.settings.top_k,
            search_params=params,
            output_fields=output_format,
        )
        return result[0]

    def process(self, inputs: MilvusInput) -> MilvusOutput:
        vector = self.embed_service.process(
            EmbedInput(
                query=inputs.query,
            ),
        )[
            0
        ]['embedding']

        retrive_output = self.execute_query(
            vector=vector,
            params=self.settings.search_params,
            output_format=self.settings.output_field,
        )

        output = [
            data['entity'][str(self.settings.output_field)] for data in retrive_output
        ]

        return MilvusOutput(output=output)
