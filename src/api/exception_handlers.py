from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.exceptions import InvalidImageError, ModelLoadError
from src.core.logging import logger


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ModelLoadError, handle_model_error)
    app.add_exception_handler(InvalidImageError, handle_invalid_image)
    app.add_exception_handler(Exception, handle_unknown_error)


async def handle_model_error(
    request: Request,
    exc: ModelLoadError,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": str(exc),
        },
    )


async def handle_invalid_image(
    request: Request,
    exc: InvalidImageError,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": str(exc),
        },
    )


async def handle_unknown_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(exc)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error",
        },
    )
