from fastapi import APIRouter, status
from shared.logging import get_logger
from api.helpers import ExceptionHandler

queries_router = APIRouter()
logger = get_logger(__name__)


@queries_router.post(
    "/query",
    tags=["querier"],
)
async def query(query: str):
    exception_handler = ExceptionHandler(
        logger=logger.bind,
        service_name=__name__,
    )

    try:
        pass
    except Exception as e:
        return exception_handler.handle_exception(
            f"Error during application initialization: {e}",
            extra={
                "query": query,
            },
        )

    try:
        pass
    except Exception as e:
        return exception_handler.handle_exception(
            str(e),
            extra={
                "query": query,
            },
        )
    return


@queries_router.get("/helthz", tags=["querier"])
async def healthz():
    """Health check endpoint"""
    return {"status": "ok"}
