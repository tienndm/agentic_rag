from __future__ import annotations

from contextlib import asynccontextmanager

from api.helpers import LoggingMiddleware
from api.router import manager_router
from domain.embedding.driver import EmbeddingDriver
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

    This asynchronous context manager initializes the embedding model on startup
    and performs a warm-up to ensure faster initial inference times.

    Args:
        app (FastAPI): The FastAPI application instance
    """
    settings = get_settings()
    driver = EmbeddingDriver(settings=settings.embed)
    driver.warm_up(num_samples=3)

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
app.include_router(manager_router)


@app.get('/')
async def index():
    """Root endpoint that redirects to the Swagger API documentation.

    Returns:
        RedirectResponse: Redirects the user to the API documentation page
    """
    return RedirectResponse(url='/docs')


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
    )
