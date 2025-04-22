from __future__ import annotations

import time

from sentence_transformers import SentenceTransformer
from shared.base.meta import SingletonMeta
from shared.logging import get_logger
from shared.settings import EmbedSettings


logger = get_logger(__name__)


class EmbeddingDriver(metaclass=SingletonMeta):
    """Driver for interacting with the sentence transformer embedding model.

    This class uses SingletonMeta to ensure that only one instance of the model
    is loaded in memory, providing thread-safe singleton behavior.

    Attributes:
        _model: The underlying SentenceTransformer model instance
        settings (EmbedSettings): Configuration settings for the embedding model
    """

    _model = None

    def __init__(self, settings: EmbedSettings = None):
        """Initialize the embedding driver.

        Args:
            settings (EmbedSettings, optional): Configuration settings. Defaults to None.
        """
        if settings is not None:
            self.settings = settings

    @property
    def embed_model(self) -> SentenceTransformer:
        """Lazy-loads and returns the embedding model.

        Returns:
            SentenceTransformer: The sentence transformer model instance
        """
        if self._model is None:
            self._model = SentenceTransformer(
                model_name_or_path=self.settings.model_name,
            )
        return self._model

    def warm_up(self, num_samples: int = 3) -> None:
        """Warm up the model with sample inference to ensure all components are initialized.

        This improves initial inference speed by running a few sample sentences
        through the model to initialize all components.

        Args:
            num_samples (int, optional): Number of warm-up samples to run. Defaults to 3.
        """
        logger.info(f'Warming up embedding model with {num_samples} sample runs...')
        start_time = time.time()

        sample_sentences = [
            'This is a sample sentence for model warm-up.',
            'Warming up the model improves initial inference speed.',
            'The quick brown fox jumps over the lazy dog.',
        ][:num_samples]

        _ = self.encode(sample_sentences)

        elapsed_time = time.time() - start_time
        logger.info(f'Model warm-up completed in {elapsed_time:.2f} seconds')

    def encode(self, sentences: list[str]) -> list:
        """Encode sentences to embeddings using the model.

        Args:
            sentences (list[str]): List of text strings to encode

        Returns:
            list: List of embedding vectors as Python lists (not numpy arrays)

        Raises:
            Exception: Re-raises any exceptions from the encoding process after logging
        """
        try:
            embeddings = self.embed_model.encode(sentences)
            return embeddings.tolist()
        except Exception as e:
            logger.exception(
                f'Error while encoding sentences: {e}',
                extra={
                    'sentences_count': len(sentences),
                },
            )
            raise
