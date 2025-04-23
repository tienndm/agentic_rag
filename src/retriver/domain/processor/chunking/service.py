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
    context: str


class ChunkingOutput(BaseModel):
    chunks: list[str]


class ChunkingService(AsyncBaseService):
    settings: ChunkingSettings
    embed_service: EmbedService

    async def process(self, inputs: ChunkingInput) -> ChunkingOutput:
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
