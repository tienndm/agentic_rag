from __future__ import annotations

import json
from typing import Any
from typing import Dict

from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMService
from infra.llm import MessageRole
from shared.logging import get_logger

from .prompt.validate_output import VALIDATE_OUTPUT_SYSTEM_PROMPT
from .prompt.validate_output import VALIDATE_OUTPUT_USER_PROMPT

logger = get_logger(__name__)


class OutputValidatorHandler:
    """
    Handler for validating the quality and sufficiency of retrieved information against the query.
    """

    llm_service: LLMService
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    async def validate_output(self, step: str, info: str) -> Dict[str, Any]:
        """
        Validate the quality and sufficiency of retrieved information against the query.

        Uses an LLM to evaluate whether the retrieved information adequately addresses
        the information need, and suggests reformulations if not.

        Args:
            step: The original query/step
            info: The retrieved information to evaluate

        Returns:
            Dict[str, Any]: Validation results with sufficiency assessment and
                          query reformulation if needed
        """
        messages = [
            CompletionMessage(
                role=MessageRole.SYSTEM,
                content=VALIDATE_OUTPUT_SYSTEM_PROMPT,
            ),
            CompletionMessage(
                role=MessageRole.USER,
                content=VALIDATE_OUTPUT_USER_PROMPT.format(step=step, info=info),
            ),
        ]

        response = await self.llm_service.process(
            LLMBaseInput(messages=messages),
        )

        self.prompt_tokens += int(response.metadata['prompt_tokens'])
        self.completion_tokens += int(response.metadata['completion_tokens'])
        self.total_tokens += int(response.metadata['total_tokens'])

        validation_result_str = response.response.strip()

        try:
            validation_result = json.loads(validation_result_str)
            logger.info(f'Validation result: {validation_result}')
            return validation_result
        except json.JSONDecodeError:
            logger.warning(
                f'Failed to parse validation result as JSON: {validation_result_str}',
            )
            return {
                'is_sufficient': True,
                'reasoning': 'Failed to parse validation result',
                'reformulated_query': step,
            }
