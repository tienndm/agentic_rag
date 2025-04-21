from __future__ import annotations

from sentence_transformers import SentenceTransformer
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import EmbedSettings


logger = get_logger(__name__)


class EmbeddingServiceInput(BaseModel):
    sentences: list[str]


class EmbeddingServiceOutput(BaseModel):
    vector: list


class EmbeddingService(BaseService):
    settings: EmbedSettings

    @property
    def embed_model(self) -> SentenceTransformer:
        return SentenceTransformer(
            model_name_or_path=self.settings.model_name,
        )

    def process(self, inputs: EmbeddingServiceInput) -> EmbeddingServiceOutput:
        try:
            embeddings = self.embed_model.encode(inputs.sentences)
            return EmbeddingServiceOutput(vector=embeddings.tolist())
        except Exception as e:
            logger.exception(
                f'Error while embedding sentences: {e}',
                extra={
                    'inputs': inputs,
                },
            )
