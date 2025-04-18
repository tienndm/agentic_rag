from __future__ import annotations

from infra.llm import LLMBaseService
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import LLMSettings


logger = get_logger(__name__)


class PlanningInput(BaseModel):
    query: str
    context: str


class PlanningOutput(BaseModel):
    answer: str
    num_tokens: int


class PlanningService(BaseService):
    llm_model: LLMBaseService
    settings: LLMSettings

    async def process(self, input: PlanningInput) -> PlanningOutput:
        raise NotImplementedError('process method not implemented')
