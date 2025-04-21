from __future__ import annotations

from functools import cached_property

from domain.embedding import EmbeddingService
from domain.embedding import EmbeddingServiceInput
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import Settings

from .base import ApplicationInput
from .base import ApplicationOutput

logger = get_logger(__name__)


class EmbedApplication(BaseService):
    settings: Settings

    @cached_property
    def embed_service(self) -> EmbeddingService:
        return EmbeddingService(settings=self.settings.embed)

    def process(self, inputs: ApplicationInput) -> ApplicationOutput:
        try:
            service_output = self.embed_service.process(
                EmbeddingServiceInput(
                    sentences=inputs.query,
                ),
            )

            # Format embeddings according to OpenAI standard
            formatted_data = [
                {'object': 'embedding', 'embedding': embedding, 'index': idx}
                for idx, embedding in enumerate(service_output.vector)
            ]

            # Create output with OpenAI standard format
            return ApplicationOutput(
                data=formatted_data,
                model=self.settings.embed.model_name,
                usage={
                    'prompt_tokens': sum(len(text.split()) for text in inputs.query),
                    'total_tokens': sum(len(text.split()) for text in inputs.query),
                },
            )
        except Exception as e:
            logger.exception(
                f'Error while embed text: {e}',
                extra={
                    'inputs': inputs,
                },
            )
            raise e
