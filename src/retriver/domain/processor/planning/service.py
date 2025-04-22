from __future__ import annotations

import json
from typing import Dict
from typing import List

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
    plan: List[Dict]
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
            plan_steps = self.parse_plan(response.response)
            logger.info(f'Plan steps: {plan_steps}')
            return PlanningOutput(
                plan=plan_steps,
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

    def parse_plan(self, plan_text: str) -> str:
        """
        Parse a plan text that might be in JSON format.
        Returns the parsed JSON as a string.
        """
        try:
            start_idx = plan_text.find('[')
            end_idx = plan_text.rfind(']') + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_text = plan_text[start_idx:end_idx]
                return json.loads(json_text)
            return plan_text
        except json.JSONDecodeError as e:
            logger.warning(f'Failed to parse plan as JSON: {e}')
            return plan_text
        except Exception as e:
            logger.warning(f'Unexpected error parsing plan: {e}')
            return plan_text
