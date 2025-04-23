from __future__ import annotations

from contextlib import asynccontextmanager

from api.helpers import LoggingMiddleware
from api.routers import retrive_router
from domain.processor.rerank import RerankService
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.logging import get_logger
from shared.logging import setup_logging
from shared.utils import get_settings
from starlette.responses import RedirectResponse

setup_logging(json_logs=False, log_level='INFO')
logger = get_logger('api')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to handle startup and shutdown events.

    This asynchronous context manager initializes the rerank model on startup
    and performs a warm-up to ensure faster initial inference times.

    Args:
        app (FastAPI): The FastAPI application instance
    """
    logger.info('Initializing RerankService singleton during application startup')
    settings = get_settings()
    RerankService(settings=settings.rerank)
    logger.info('RerankService initialized and model warmed up')

    yield


app = FastAPI(
    title='Agentic-RAG API',
    description='API for Agentic-RAG',
    version='0.1.0',
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware, logger=logger)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(retrive_router, prefix='/api/v1', tags=['retrive'])


@app.get('/')
async def index():
    return RedirectResponse(url='/docs')


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8001,
    )
