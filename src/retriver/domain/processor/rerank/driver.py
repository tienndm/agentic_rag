from __future__ import annotations

import numpy as np
from sentence_transformers import CrossEncoder
from shared.base import SingletonMeta
from shared.logging import get_logger
from shared.settings import RerankSettings


logger = get_logger(__name__)


class RerankDriver(metaclass=SingletonMeta):
    _model = None

    def __init__(self, settings: RerankSettings = None):
        if settings is not None:
            self.settings = settings

    @property
    def rerank_model(self) -> CrossEncoder:
        if self._model is None:
            self._model = CrossEncoder(
                model_name_or_path=self.settings.model_name,
            )
        return self._model

    def predict(self, hits_pairs: list[list[str]]) -> np.ndarray:
        try:
            scores = self.rerank_model.predict(hits_pairs)
            return scores
        except Exception as e:
            logger.exception(
                f'Error when reranking hits pairs: {e}',
            )
            raise
