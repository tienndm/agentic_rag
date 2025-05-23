from __future__ import annotations

import json
from typing import Any
from typing import Dict

from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMService
from infra.llm import MessageRole
from shared.base import BaseService
from shared.logging import get_logger

from .prompt.validate_output import VALIDATE_OUTPUT_SYSTEM_PROMPT
from .prompt.validate_output import VALIDATE_OUTPUT_USER_PROMPT

logger = get_logger(__name__)


class OutputValidatorHandler(BaseService):
    """
    Handler for validating the quality and sufficiency of retrieved information against the query.
    """

    llm_service: LLMService

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    async def process(self, step: str, info: str) -> Dict[str, Any]:
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
            try:
                import re

                json_pattern = r'(\{.*?\})'
                match = re.search(json_pattern, validation_result_str, re.DOTALL)
                if match:
                    cleaned_json = match.group(1)
                    validation_result = json.loads(cleaned_json)
                    logger.info(
                        f'Validation result: {validation_result}',
                    )
                    return validation_result
            except Exception as e2:
                logger.warning(f'Failed second attempt to parse JSON: {str(e2)}')

            return {
                'is_sufficient': True,
                'reasoning': 'Failed to parse validation result',
                'reformulated_query': step,
            }
