from __future__ import annotations

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
    excepttion_handler = ExceptionHandler(
        logger=logger.bind(),
        service_name=__name__,
    )

    try:
        pass
    except Exception as e:
        return excepttion_handler.handle_exception(
            f'Error during application initialization: {e}',
            extra={},
        )

    try:
        pass
    except Exception as e:
        return excepttion_handler.handle_exception(
            f'Error during application initialization: {e}',
            extra={'inputs': inputs},
        )
    return excepttion_handler.handle_success('Success', extra={})


@retrive_router.get('/helthz', tags=['retriver'])
async def healthz():
    """Health check endpoint"""
    return {'status': 'ok'}
