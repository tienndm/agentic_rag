from __future__ import annotations

from typing import Optional

from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMBaseService
from infra.llm import MessageRole
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger

from .prompt.planning import SYSTEM_PROMPT
from .prompt.planning import USER_PROMPT

logger = get_logger(__name__)


class PlanningInput(BaseModel):
    query: str
    fact: str
    previous_plan: Optional[str] = None
    previous_error: Optional[str] = None


class PlanningOutput(BaseModel):
    plan: str
    metadata: dict[str, str] | None = None


class PlanningService(BaseService):
    llm_model: LLMBaseService

    async def process(self, inputs: PlanningInput) -> PlanningOutput | None:
        try:
            messages = [
                CompletionMessage(
                    role=MessageRole.SYSTEM,
                    content=SYSTEM_PROMPT,
                ),
                CompletionMessage(
                    role=MessageRole.USER,
                    content=USER_PROMPT.format(query=inputs.query, fact=inputs.fact),
                ),
            ]

        except Exception as e:
            logger.exception(
                f'Error while creating message: {e}',
                extra={
                    'inputs': inputs,
                },
            )
            raise e

        try:
            response = await self.llm_model.process(
                LLMBaseInput(
                    messages=messages,
                ),
            )
            return PlanningOutput(
                plan=response.response,
                metadata=response.metadata,
            )
        except Exception as e:
            logger.exception(
                f'Error while planing: {e}',
                extra={
                    'inputs': inputs,
                },
            )
            raise e
