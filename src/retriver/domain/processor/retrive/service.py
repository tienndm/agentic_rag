from __future__ import annotations

from infra.milvus_clone import MilvusService
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger


logger = get_logger(__name__)


class RetriveInput(BaseModel):
    query: list[str]
    collection_name: str
    top_k: int


class RetriveOutput(BaseModel):
    context: list[str]


class RetriveService(BaseService):
    milvus_service: MilvusService

    async def process(self, inputs: RetriveInput) -> RetriveOutput:
        try:
            # TODO embed inputs query by using 3th party service
            query_vector = None
            context = self.milvus_service.batch_search(
                collection_name=inputs.collection_name,
                query_vectors=query_vector,
            )

            return RetriveOutput(context=context)
        except Exception as e:
            logger.exception(
                f'Error while retriving data from vector db: {e}',
                extra={
                    'inputs': inputs,
                },
            )
