from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.api.dependencies import initialize_services
from src.api.exception_handlers import register_exception_handlers
from src.api.middleware import register_middleware
from src.api.routes import router
from src.core.logging import logger


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator[None, None]:
    logger.info("Initializing application services...")
    initialize_services()
    logger.info("Application started successfully.")

    yield

    logger.info("Application shutdown.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Smart Retail Shelf Monitoring",
        description="Production-ready Computer Vision API for Retail Shelf Monitoring",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(router)
    register_middleware(app)
    register_exception_handlers(app)

    return app
