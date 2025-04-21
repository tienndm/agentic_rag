from __future__ import annotations

from infra.llm import LLMBaseService
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import LLMSettings


logger = get_logger(__name__)


class RerankInput(BaseModel):
    query: str
    context: str


class RerankOutput(BaseModel):
    answer: str
    num_tokens: int


class RerankService(BaseService):
    llm_model: LLMBaseService
    settings: LLMSettings

    async def process(self, input: RerankInput) -> RerankOutput:
        raise NotImplementedError('process method not implemented')
