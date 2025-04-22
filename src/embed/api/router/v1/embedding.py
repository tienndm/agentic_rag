from __future__ import annotations

from application.embed import ApplicationInput
from application.embed import EmbedApplication
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from shared.logging import get_logger
from shared.utils import get_settings

from ...helpers.exception_handler import ExceptionHandler
from ...models.embedding import EmbedInput

embed_router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

logger.info(settings)


@embed_router.post('/embed', tags=['embed'])
async def embedding(inputs: EmbedInput) -> JSONResponse:
    """Generate embeddings for a list of text strings.

    This endpoint transforms text inputs into vector embeddings using the configured
    embedding model. These embeddings can be used for semantic search, clustering,
    or other NLP applications within a RAG (Retrieval-Augmented Generation) system.

    Args:
        inputs (EmbedInput): Input model containing a list of text strings to embed

    Returns:
        JSONResponse: JSON response with embedding vectors and usage information

    Raises:
        Exception: Any exceptions during application initialization or processing
                  are caught and handled through the exception_handler
    """
    exception_handler = ExceptionHandler(
        logger=logger.bind(),
        service_name=__name__,
    )

    try:
        application = EmbedApplication(settings=settings)
    except Exception as e:
        return exception_handler.handle_exception(
            f'Error while application initialization: {e}',
            extra={
                'inputs': inputs,
            },
        )

    try:
        output = application.process(
            inputs=ApplicationInput(
                query=inputs.query,
            ),
        )
    except Exception as e:
        return exception_handler.handle_exception(
            f'Error while process application: {e}',
            extra={
                'inputs': inputs,
            },
        )
    return exception_handler.handle_success(output.model_dump())
