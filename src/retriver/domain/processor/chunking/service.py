from __future__ import annotations

import nltk
from infra.embed import EmbedInput
from infra.embed import EmbedService
from shared.base import AsyncBaseService
from shared.base import BaseModel
from shared.logging import get_logger
from shared.settings import ChunkingSettings
from sklearn.metrics.pairwise import cosine_similarity

try:
    nltk.download('punkt')
    nltk.download('punkt_tab')
except Exception:
    pass

logger = get_logger(__name__)


class ChunkingInput(BaseModel):
    """
    Input for the text chunking process.

    Attributes:
        context: The raw text content to be chunked
    """

    context: str


class ChunkingOutput(BaseModel):
    """
    Output from the text chunking process.

    Attributes:
        chunks: The resulting text chunks after processing
    """

    chunks: list[str]


class ChunkingService(AsyncBaseService):
    """
    Service for intelligently chunking text based on semantic similarity.

    This service divides input text into semantically coherent chunks by:
    1. Splitting text into sentences
    2. Computing embeddings for each sentence
    3. Grouping sentences based on their semantic similarity

    This approach preserves semantic relationships better than naive
    character or token-based chunking strategies, resulting in more
    meaningful context during retrieval.
    """

    settings: ChunkingSettings
    embed_service: EmbedService

    async def process(self, inputs: ChunkingInput) -> ChunkingOutput:
        """
        Process text into semantically coherent chunks.

        This method implements a semantic chunking algorithm that:
        1. Splits text into individual sentences
        2. Computes vector embeddings for each sentence
        3. Groups adjacent sentences based on their semantic similarity
        4. Forms chunks by combining semantically similar sentences

        The similarity threshold controls how aggressively sentences are combined,
        allowing tuning between larger chunks with potentially less precision and
        smaller, more focused chunks.

        Args:
            inputs: Input containing the text to be chunked

        Returns:
            ChunkingOutput: Contains the resulting text chunks
        """
        sentences = nltk.sent_tokenize(inputs.context)
        if not sentences:
            return ChunkingOutput(chunks=[])

        embed_response = await self.embed_service.process(EmbedInput(query=sentences))

        if not embed_response.embeddings:
            return ChunkingOutput(chunks=[])

        embeddings = embed_response.embeddings

        chunks = []
        current_chunk = [sentences[0]]
        for i in range(1, len(sentences)):
            similarity = cosine_similarity([embeddings[i - 1]], [embeddings[i]])[0][0]

            if similarity >= self.settings.similarity_threshold:
                current_chunk.append(sentences[i])
            else:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentences[i]]

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return ChunkingOutput(chunks=chunks)
