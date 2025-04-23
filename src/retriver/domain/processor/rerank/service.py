from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from sentence_transformers import CrossEncoder
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import RerankSettings


logger = get_logger(__name__)


class RerankInput(BaseModel):
    query: str
    hits: List[Dict[str, Any]]


class RerankOutput(BaseModel):
    ranked_contexts: List[Dict[str, Any]]


class RerankService(BaseService):
    settings: RerankSettings
    _model: Optional[CrossEncoder] = None
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """Singleton pattern implementation"""
        if cls._instance is None:
            logger.info('Creating singleton instance of RerankService')
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, settings=None):
        """Initialize only once when the instance is first created"""
        if not self.__class__._initialized:
            super().__init__()
            if settings is not None:
                self.settings = settings
                self._initialize_model()
            self.__class__._initialized = True
            logger.info('RerankService initialized')

    def _initialize_model(self) -> None:
        """Initialize and warm up the model during service creation"""
        if not hasattr(self, 'settings') or self.settings is None:
            logger.warning('Cannot initialize model: settings not provided')
            return

        logger.info(f'Loading reranking model: {self.settings.model_name}')
        self._model = CrossEncoder(self.settings.model_name)
        self._warm_up_model()

    def _warm_up_model(self) -> None:
        """Warm up the model with a dummy query to ensure faster first inference"""
        if self._model is None:
            logger.warning('Cannot warm up model: model not initialized')
            return

        try:
            dummy_query = 'This is a warm up query'
            dummy_context = 'This is a warm up context'
            self._model.predict([[dummy_query, dummy_context]])
            logger.debug('Model warm-up completed successfully')
        except Exception as e:
            logger.warning(f'Model warm-up failed: {e}')

    @property
    def model(self) -> CrossEncoder:
        """Ensure model is initialized before access"""
        if self._model is None:
            self._initialize_model()
            if self._model is None:
                raise ValueError('Failed to initialize the reranking model')
        return self._model

    async def process(self, inputs: RerankInput) -> RerankOutput:
        """
        Rerank the retrieved contexts based on relevance to the query using a Cross-Encoder model.

        Args:
            input: RerankInput object containing query and contexts

        Returns:
            RerankOutput object with ranked contexts
        """
        try:
            all_hits_with_index = []
            for hit_idx, hit in enumerate(inputs.hits):
                chunks = hit['chunks'] if isinstance(hit, dict) else hit.chunks
                for chunk in chunks:
                    all_hits_with_index.append((hit_idx, chunk))

            hits_pairs = [[inputs.query, chunk] for _, chunk in all_hits_with_index]

            if not hits_pairs:
                logger.warning('No chunks found in hits, skipping reranking')
                return RerankOutput(ranked_contexts=inputs.hits)

            scores = self.model.predict(hits_pairs)

            hit_scores = {}
            hit_counts = {}

            for i, (hit_idx, _) in enumerate(all_hits_with_index):
                hit_scores[hit_idx] = hit_scores.get(hit_idx, 0) + float(scores[i])
                hit_counts[hit_idx] = hit_counts.get(hit_idx, 0) + 1

            for i, hit in enumerate(inputs.hits):
                if isinstance(hit, dict):
                    if i in hit_scores:
                        hit['reranking_score'] = hit_scores[i] / hit_counts[i]
                    else:
                        hit['reranking_score'] = 0.0
                else:
                    if i in hit_scores:
                        hit.reranking_score = hit_scores[i] / hit_counts[i]
                    else:
                        hit.reranking_score = 0.0

            def get_score(item):
                return (
                    item['reranking_score']
                    if isinstance(item, dict)
                    else item.reranking_score
                )

            ranked_hits = sorted(inputs.hits, key=get_score, reverse=True)

            return RerankOutput(ranked_contexts=ranked_hits)

        except Exception as e:
            logger.exception(
                f'Error while reranking contexts: {e}',
            )
            return RerankOutput(ranked_contexts=inputs.hits)
