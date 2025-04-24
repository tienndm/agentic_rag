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
"""
Planning Service Module

This module provides functionality for generating structured retrieval plans
based on user queries and extracted facts, enabling strategic information gathering.
"""

logger = get_logger(__name__)


class PlanningInput(BaseModel):
    """
    Input model for the Planning service.

    Attributes:
        query (str): The original user query to plan for.
        fact (str): Extracted facts from the query to focus planning on.
    """

    query: str
    fact: str


class PlanningOutput(BaseModel):
    """
    Output model for the Planning service.

    Attributes:
        plan (List[Dict]): The generated execution plan as a list of steps.
        metadata (dict[str, str] | None): Optional metadata about the plan generation.
    """

    plan: List[Dict]
    metadata: dict[str, str] | None = None


class PlanningService(BaseService):
    """
    Service responsible for generating structured retrieval plans.

    This service takes a user query and extracted facts, then uses an LLM
    to create a step-by-step plan for retrieving the necessary information.
    The plan guides subsequent retrieval operations by breaking down complex
    information needs into manageable steps.

    Attributes:
        llm_model (LLMBaseService): The language model service used for plan generation.
    """

    llm_model: LLMBaseService

    async def process(self, inputs: PlanningInput) -> PlanningOutput | None:
        """
        Generate a structured retrieval plan based on the input query and facts.

        This method constructs prompt messages for the LLM that guide it to create
        a strategic plan for retrieving information needed to answer the query.
        The resulting plan consists of discrete steps, each targeting specific
        information needs.

        Args:
            inputs (PlanningInput): The input containing query and extracted facts.

        Returns:
            PlanningOutput: The generated plan as a structured object.

        Raises:
            Exception: If there's an error during message creation or plan generation.
        """
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

        This method attempts to extract and parse JSON content from the
        LLM's response, handling various formats and potential errors.

        Args:
            plan_text (str): The raw plan text from the LLM.

        Returns:
            str: The parsed JSON plan as a string, or the original text if parsing fails.
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
