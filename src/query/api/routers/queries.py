from __future__ import annotations

from application.query_service import ApplicationInput
from application.query_service import QuerierService
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from shared.logging import get_logger
from shared.utils import get_settings

from ..helpers import ExceptionHandler
from ..models.queries import QuerierInput

queries_router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


@queries_router.post(
    '/query',
    tags=['querier'],
)
async def query(inputs: QuerierInput) -> JSONResponse:
    exception_handler = ExceptionHandler(
        logger=logger.bind(),
        service_name=__name__,
    )

    try:
        application = QuerierService(settings=settings)
    except Exception as e:
        return exception_handler.handle_exception(
            f'Error during application initialization: {e}',
            extra={
                'query': query,
            },
        )

    try:
        inputs = ApplicationInput(
            query=inputs.query,
        )
        output = await application.process(inputs)
    except Exception as e:
        return exception_handler.handle_exception(
            str(e),
            extra={
                'query': query,
            },
        )
    return exception_handler.handle_success(output.model_dump())


@queries_router.get('/helthz', tags=['querier'])
async def healthz():
    """Health check endpoint"""
    return {'status': 'ok'}
