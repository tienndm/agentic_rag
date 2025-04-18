from __future__ import annotations

from api.helpers import LoggingMiddleware
from api.routers import queries_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.logging import get_logger
from shared.logging import setup_logging
from starlette.responses import RedirectResponse

setup_logging(json_logs=False, log_level='ERROR')
logger = get_logger('api')

app = FastAPI(
    title='Agentic-RAG API',
    description='API for Agentic-RAG',
    version='0.1.0',
)

app.add_middleware(LoggingMiddleware, logger=logger)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(queries_router, prefix='/api/v1', tags=['querier'])


@app.get('/')
async def index():
    return RedirectResponse(url='/docs')


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
    )
