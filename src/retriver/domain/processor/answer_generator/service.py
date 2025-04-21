from __future__ import annotations

from infra.llm import CompletionMessage
from infra.llm import LLMBaseService
from infra.llm import MessageRole
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger

from .prompt.answer_generator import SYSTEM_MESSAGE
from .prompt.answer_generator import USER_MESSAGE

logger = get_logger(__name__)


class AnswerGeneratorInput(BaseModel):
    query: str
    context: str


class AnswerGeneratorOutput(BaseModel):
    answer: str
    metadata: dict[str, str] | None = None
    error: str | None = None


class AnswerGenerator(BaseService):
    llm_model: LLMBaseService

    async def process(self, input: AnswerGeneratorInput) -> AnswerGeneratorOutput:
        try:
            message = [
                CompletionMessage(
                    role=MessageRole.SYSTEM,
                    content=SYSTEM_MESSAGE,
                ),
                CompletionMessage(
                    role=MessageRole.USER,
                    content=USER_MESSAGE.format(
                        query=input.query,
                        context=input.context,
                    ),
                ),
            ]
        except Exception as e:
            logger.exception(
                f'Error during creating message: {e}',
                extra={
                    'input': input,
                },
            )
            raise e

        try:
            response = await self.llm_model.process(
                messages=message,
            )

            return AnswerGeneratorOutput(
                answer=response.response,
                metadata=response.metadata,
            )
        except Exception as e:
            logger.exception(
                f'Error during generating answer: {e}',
                extra={
                    'input': input,
                },
            )
            raise e
