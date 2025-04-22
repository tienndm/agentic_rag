from __future__ import annotations

from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import EmbedSettings

from .driver import EmbeddingDriver


logger = get_logger(__name__)


class EmbeddingServiceInput(BaseModel):
    """Input model for the embedding service.

    Attributes:
        sentences (list[str]): List of text strings to be converted to embeddings
    """

    sentences: list[str]


class EmbeddingServiceOutput(BaseModel):
    """Output model for the embedding service.

    Attributes:
        vector (list): List of embedding vectors generated from the input sentences
    """

    vector: list


class EmbeddingService(BaseService):
    """Service for generating text embeddings using the configured embedding model.

    This service acts as a business logic layer between the API and the actual
    embedding driver that interfaces with the embedding model.

    Attributes:
        settings (EmbedSettings): Configuration settings for the embedding service
    """

    settings: EmbedSettings

    @property
    def driver(self) -> EmbeddingDriver:
        """Returns an instance of the embedding driver.

        Returns:
            EmbeddingDriver: Driver for interacting with the embedding model
        """
        return EmbeddingDriver(settings=self.settings)

    def process(self, inputs: EmbeddingServiceInput) -> EmbeddingServiceOutput:
        """Process input sentences and generate embeddings.

        Args:
            inputs (EmbeddingServiceInput): Input model containing sentences to embed

        Returns:
            EmbeddingServiceOutput: Output model containing the generated embeddings

        Raises:
            Exception: Re-raises any exceptions from the embedding process after logging
        """
        try:
            embeddings = self.driver.encode(inputs.sentences)
            return EmbeddingServiceOutput(vector=embeddings)
        except Exception as e:
            logger.exception(
                f'Error while embedding sentences: {e}',
                extra={
                    'inputs': inputs,
                },
            )
            raise
