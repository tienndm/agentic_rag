from __future__ import annotations

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


class PlanningOutput(BaseModel):
    # plan: list[str]
    plan: str
    metadata: dict[str, str] | None = None


class PlanningService(BaseService):
    llm_model: LLMBaseService

    def parse_plan(self, output: str) -> list[str]:
        """
        Parse the planning output into a list of individual steps.

        Args:
            output (str): The raw output from the planning prompt

        Returns:
            List[str]: List of extracted step contents
        """
        output = output.strip()

        steps = []
        step_markers = [marker for marker in output.split('[step') if marker.strip()]
        for marker in step_markers:
            parts = marker.split(']', 1)
            if len(parts) > 1:
                step_content = parts[1].strip()
                steps.append(step_content)

        return steps

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
            # plan_steps = self.parse_plan(response.response)
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
