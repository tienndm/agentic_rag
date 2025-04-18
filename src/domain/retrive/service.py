from shared.base import BaseModel, BaseService
from shared.logging import get_logger
from shared.settings import LLMSettings
from infra.llm import LLMBaseService


logger = get_logger(__name__)


class RetriveInput(BaseModel):
    query: str
    context: str


class RetriveOutput(BaseModel):
    answer: str
    num_tokens: int


class RetriveService(BaseService):
    llm_model: LLMBaseService
    settings: LLMSettings

    async def process(self, input: RetriveInput) -> RetriveOutput:
        raise NotImplementedError("process method not implemented")
