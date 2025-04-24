from __future__ import annotations

from application.retriver_application import ApplicationInput
from application.retriver_application import RetriveApplication
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from shared.logging import get_logger
from shared.utils import get_settings

from ..helpers.exception_handler import ExceptionHandler
from ..models.retriver import RetriveInput

logger = get_logger(__name__)
retrive_router = APIRouter()
settings = get_settings()


@retrive_router.post('/retrive', tags=['retrive'])
async def retrive(inputs: RetriveInput) -> JSONResponse:
    """
    Main retrieval endpoint that processes user queries using the RAG pipeline.

    This endpoint:
    1. Takes a user query as input
    2. Initializes the retrieval application with appropriate settings
    3. Processes the query through the complete RAG pipeline
    4. Returns the generated answer with appropriate status codes

    Args:
        inputs: RetriveInput object containing the user's query

    Returns:
        JSONResponse: Contains the generated answer and success/error messages

    Raises:
        Exception: Handled internally for application initialization or processing errors
    """
    excepttion_handler = ExceptionHandler(
        logger=logger.bind(),
        service_name=__name__,
    )

    try:
        application = RetriveApplication(settings=settings)
    except Exception as e:
        return excepttion_handler.handle_exception(
            f'Error during application initialization: {e}',
            extra={},
        )

    try:
        response = await application.process(
            inputs=ApplicationInput(
                query=inputs.query,
            ),
        )
    except Exception as e:
        return excepttion_handler.handle_exception(
            f'Error during application initialization: {e}',
            extra={'inputs': inputs},
        )
    return excepttion_handler.handle_success(response.model_dump())


@retrive_router.get('/helthz', tags=['retriver'])
async def healthz():
    """Health check endpoint"""
    return {'status': 'ok'}
