from __future__ import annotations

from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMBaseService
from infra.llm import MessageRole
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger

from .prompt.get_fact import SYSTEM_PROMPT
from .prompt.get_fact import USER_PROMPT


logger = get_logger(__name__)


class GetFactInput(BaseModel):
    query: str


class GetFactOutput(BaseModel):
    fact: str
    metadata: dict[str, str] | None = None


class GetFactService(BaseService):
    llm_model: LLMBaseService

    async def process(self, inputs: GetFactInput) -> GetFactOutput:
        try:
            messages = [
                CompletionMessage(
                    role=MessageRole.SYSTEM,
                    content=SYSTEM_PROMPT,
                ),
                CompletionMessage(
                    role=MessageRole.USER,
                    content=USER_PROMPT.format(query=inputs.query),
                ),
            ]
        except Exception as e:
            logger.exception(
                f'Error during creating message: {e}',
                extra={
                    'input': inputs,
                },
            )
            raise e

        try:
            response = await self.llm_model.process(
                LLMBaseInput(
                    messages=messages,
                ),
            )
            return GetFactOutput(
                fact=response.response,
                metadata=response.metadata,
            )
        except Exception as e:
            logger.exception(
                f'Error while getting fact: {e}',
                extra={'inputs': inputs},
            )
            raise e
