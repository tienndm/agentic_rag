from __future__ import annotations

from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMBaseService
from infra.llm import MessageRole
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger

from .prompt.router_prompt import ROUTER_SYSTEM_PROMPT


logger = get_logger(__name__)


class BaseRouterInput(BaseModel):
    """Base input model for router services."""

    query: str


class BaseRouterOutput(BaseModel):
    """Base output model for router services."""

    route: str = None
    metadata: dict[str, str] = {}
    error: str | None = None


class RouterServiceV1(BaseService):
    llm_model: LLMBaseService

    async def process(self, inputs: BaseRouterInput) -> BaseRouterOutput:
        try:
            messages = [
                CompletionMessage(
                    role=MessageRole.SYSTEM,
                    content=ROUTER_SYSTEM_PROMPT,
                ),
                CompletionMessage(
                    role=MessageRole.USER,
                    content=inputs.query,
                ),
            ]
        except Exception as e:
            logger.exception(
                f'Error occured while creating messages: {e}',
                extra={'inputs': inputs},
            )
            raise e

        try:
            response = await self.llm_model.process(
                LLMBaseInput(
                    messages=messages,
                ),
            )
            return BaseRouterOutput(
                route=response.response,
                metadata=response.metadata,
            )

        except Exception as e:
            logger.exception(
                f'Error occured while routings: {e}',
                extra={'inputs': inputs},
            )
            raise e
