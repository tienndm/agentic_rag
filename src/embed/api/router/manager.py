from __future__ import annotations

from fastapi import APIRouter
from shared.logging import get_logger
from shared.utils import get_settings

from .v1.embedding import embed_router

manager_router = APIRouter(prefix='/v1')
logger = get_logger(__name__)
settings = get_settings()

manager_router.include_router(embed_router, tags=['Embed'])


@manager_router.get('/healthz')
async def healthz():
    return {'status': 'ok'}
