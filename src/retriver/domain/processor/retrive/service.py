from __future__ import annotations

from infra.milvus import MilvusInput
from infra.milvus import MilvusService
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger


logger = get_logger(__name__)


class RetriveInput(BaseModel):
    query: list[str]


class RetriveOutput(BaseModel):
    context: list[str]


class RetriveService(BaseService):
    milvus_service: MilvusService

    async def process(self, inputs: RetriveInput) -> RetriveOutput:
        try:
            context = self.milvus_service.process(
                MilvusInput(
                    query=inputs.query,
                ),
            )
            return RetriveOutput(context=context)
        except Exception as e:
            logger.exception(
                f'Error while retriving data from vector db: {e}',
                extra={
                    'inputs': inputs,
                },
            )
