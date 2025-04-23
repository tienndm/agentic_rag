from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List

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

    @property
    def model(self) -> CrossEncoder:
        return CrossEncoder(self.settings.model_name)

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
