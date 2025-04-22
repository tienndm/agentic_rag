from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List

from sentence_transformers import CrossEncoder
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import Settings


logger = get_logger(__name__)


class RerankInput(BaseModel):
    query: str
    contexts: List[Dict[str, Any]]
    top_k: int = 3


class RerankOutput(BaseModel):
    ranked_contexts: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}


class RerankService(BaseService):
    settings: Settings

    @property
    def model(self) -> CrossEncoder:
        return CrossEncoder(self.settings.rerank.model_name)

    async def process(self, input: RerankInput) -> RerankOutput:
        """
        Rerank the retrieved contexts based on relevance to the query using a Cross-Encoder model.

        Args:
            input: RerankInput object containing query and contexts

        Returns:
            RerankOutput object with ranked contexts
        """
        try:
            logger.info(
                f'Reranking {len(input.contexts)} contexts for query: {input.query}',
            )

            # Use Cross-Encoder for reranking
            ranked_contexts = await self._rerank_contexts(input.query, input.contexts)

            # Return top_k results
            top_results = ranked_contexts[: input.top_k]

            return RerankOutput(
                ranked_contexts=top_results,
                metadata={
                    'total_contexts': len(input.contexts),
                    'returned_contexts': len(top_results),
                    'model_name': self.model_name,
                    'model_type': 'cross-encoder',
                },
            )

        except Exception as e:
            logger.exception(
                f'Error while reranking contexts: {e}',
                extra={
                    'query': input.query,
                    'num_contexts': len(input.contexts),
                },
            )
            raise e

    async def _rerank_contexts(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Rerank contexts using Cross-Encoder model which directly predicts the relevance
        between query and context pairs.

        Args:
            query: The user query
            contexts: List of context items with content and metadata

        Returns:
            Reranked list of contexts
        """
        if not contexts:
            return []

        text_pairs = []
        for ctx in contexts:
            content = ctx.get('full_content', ctx.get('content', ''))
            content = content[:5000] if len(content) > 5000 else content
            text_pairs.append([query, content])

        scores = self.model.predict(text_pairs)

        scored_pairs = [(float(scores[i]), i) for i in range(len(contexts))]
        scored_pairs.sort(key=lambda x: x[0], reverse=True)

        ranked_contexts = []
        for score, idx in scored_pairs:
            context_with_score = {**contexts[idx], 'relevance_score': score}
            ranked_contexts.append(context_with_score)

        return ranked_contexts
