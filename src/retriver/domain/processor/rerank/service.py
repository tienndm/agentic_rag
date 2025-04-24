from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List

from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import RerankSettings

from .driver import RerankDriver


logger = get_logger(__name__)


class RerankInput(BaseModel):
    """
    Input for the reranking process.

    Attributes:
        query: The original query to rank results against
        hits: List of retrieved context items to be reranked
    """

    query: str
    hits: List[Dict[str, Any]]


class RerankOutput(BaseModel):
    """
    Output from the reranking process.

    Attributes:
        ranked_contexts: The reranked list of context items
    """

    ranked_contexts: List[Dict[str, Any]]


class RerankService(BaseService):
    """
    Service for reranking retrieved contexts based on relevance to the query.

    This service uses a cross-encoder model to assess the semantic relevance
    between a query and retrieved documents, then reranks them to prioritize
    the most relevant information. The reranking step significantly enhances
    the quality of context provided to the LLM for answer generation by:

    1. Evaluating query-document relevance using advanced language models
    2. Reordering documents to focus on the most pertinent information
    3. Improving the overall quality of generated responses

    This represents an important step in the RAG pipeline that bridges
    efficient retrieval with precision.
    """

    settings: RerankSettings

    @property
    def driver(self) -> RerankDriver:
        """
        Returns the RerankDriver singleton instance.

        The driver manages the underlying cross-encoder model and performs
        the actual inference for reranking.

        Returns:
            RerankDriver: The rerank driver instance
        """
        return RerankDriver(settings=self.settings)

    async def process(self, inputs: RerankInput) -> RerankOutput:
        """
        Rerank the retrieved contexts based on relevance to the query.

        This method:
        1. Extracts all text chunks from retrieved contexts
        2. Creates query-chunk pairs for scoring
        3. Computes relevance scores using a cross-encoder model
        4. Aggregates scores per document and normalizes them
        5. Sorts documents based on their relevance scores

        The scoring approach supports both individual chunks and full documents,
        with scores aggregated for multi-chunk documents.

        Args:
            inputs: RerankInput object containing query and contexts

        Returns:
            RerankOutput: Container with reranked contexts
        """
        try:
            all_hits_with_index = []
            for hit_idx, hit in enumerate(inputs.hits):
                chunks = hit['chunks'] if isinstance(hit, dict) else hit.chunks
                for chunk in chunks:
                    all_hits_with_index.append((hit_idx, chunk))

            hits_pairs = [[inputs.query, chunk] for _, chunk in all_hits_with_index]

            scores = self.driver.predict(hits_pairs)

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
