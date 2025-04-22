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
    """Application layer for handling embedding requests.

    This class serves as an intermediary between the API layer and the domain service layer,
    transforming API inputs into service inputs and service outputs into API outputs.
    It formats the embedding results into a structure compatible with common embedding APIs.

    Attributes:
        settings (Settings): Application configuration settings
    """

    settings: Settings

    @cached_property
    def embed_service(self) -> EmbeddingService:
        """Lazily initialized embedding service instance.

        Returns:
            EmbeddingService: Service for generating text embeddings
        """
        return EmbeddingService(settings=self.settings.embed)

    def process(self, inputs: ApplicationInput) -> ApplicationOutput:
        """Process embedding requests and format the results.

        Transforms the input text strings into embeddings via the embedding service,
        then formats the embeddings into a standardized API response format.

        Args:
            inputs (ApplicationInput): Application input containing query text strings

        Returns:
            ApplicationOutput: Formatted embedding results with metadata

        Raises:
            Exception: Re-raises any exceptions from the embedding process after logging
        """
        try:
            service_output = self.embed_service.process(
                EmbeddingServiceInput(
                    sentences=inputs.query,
                ),
            )

            formatted_data = [
                {'object': 'embedding', 'embedding': embedding, 'index': idx}
                for idx, embedding in enumerate(service_output.vector)
            ]

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
