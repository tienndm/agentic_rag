from __future__ import annotations

from infra.llm import LLMBaseService
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import LLMSettings


logger = get_logger(__name__)


class WebSearchingInput(BaseModel):
    query: str
    context: str


class WebSearchingOutput(BaseModel):
    answer: str
    num_tokens: int


class WebSearchingService(BaseService):
    llm_model: LLMBaseService
    settings: LLMSettings

    async def process(self, input: WebSearchingInput) -> WebSearchingOutput:
        raise NotImplementedError('process method not implemented')
