"""
Application Entry Point

Responsibilities
----------------
- Create FastAPI application
- Initialize services
- Configure middleware
- Register exception handlers
- Register API routes
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.dependencies import initialize_services
from src.api.routes import router
from src.core.exceptions import (
    InvalidImageError,
    ModelLoadError,
)
from src.core.logging import logger


# --------------------------------------------------------
# Lifespan
# --------------------------------------------------------

@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator[None, None]:

    logger.info("Initializing application services...")

    initialize_services()

    logger.info("Application started successfully.")

    yield

    logger.info("Application shutdown.")


# --------------------------------------------------------
# FastAPI App
# --------------------------------------------------------

app = FastAPI(
    title="Smart Retail Shelf Monitoring",
    description="Production-ready Computer Vision API for Retail Shelf Monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


# --------------------------------------------------------
# Middleware
# --------------------------------------------------------

@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):

    correlation_id = str(uuid.uuid4())

    start = time.perf_counter()

    response = await call_next(request)

    latency = (
        time.perf_counter() - start
    ) * 1000

    response.headers[
        "X-Correlation-ID"
    ] = correlation_id

    logger.info(
        "[%s] %s %.2f ms",
        request.method,
        request.url.path,
        latency,
    )

    return response


# --------------------------------------------------------
# Exception Handlers
# --------------------------------------------------------

@app.exception_handler(ModelLoadError)
async def handle_model_error(
    request: Request,
    exc: ModelLoadError,
):

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": str(exc),
        },
    )


@app.exception_handler(InvalidImageError)
async def handle_invalid_image(
    request: Request,
    exc: InvalidImageError,
):

    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": str(exc),
        },
    )


@app.exception_handler(Exception)
async def handle_unknown_error(
    request: Request,
    exc: Exception,
):

    logger.exception(exc)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error",
        },
    )


# --------------------------------------------------------
# Run
# --------------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    from src.core.config import get_settings

    settings = get_settings()

    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )