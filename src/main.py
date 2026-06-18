"""
FastAPI Entry Point

Responsibilities
----------------
- Application lifecycle
- Middleware
- Exception handling
- Route registration

Business logic is delegated to ShelfMonitoringService.
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import torch
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse

from src.core.exceptions import (
    InvalidImageError,
    ModelLoadError,
)
from src.core.logging import logger
from src.core.config import get_settings

from src.models.schemas import InferenceResponse

from src.services.detection import YOLOInferenceEngine
from src.services.shelf_service import ShelfMonitoringService

# --------------------------------------------------------
# Global Services
# --------------------------------------------------------

detector: YOLOInferenceEngine | None = None
shelf_service: ShelfMonitoringService | None = None


# --------------------------------------------------------
# Application Lifespan
# --------------------------------------------------------

@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator:

    global detector
    global shelf_service

    logger.info("Loading YOLO model...")

    detector = YOLOInferenceEngine()

    detector.warmup()

    shelf_service = ShelfMonitoringService(detector)

    logger.info("Application started.")

    yield

    logger.info("Application shutdown.")


# --------------------------------------------------------
# FastAPI
# --------------------------------------------------------

app = FastAPI(
    title="Smart Retail Shelf Monitoring",
    version="1.0.0",
    description="YOLOv11 Retail Shelf Monitoring API",
    lifespan=lifespan,
)


# --------------------------------------------------------
# Middleware
# --------------------------------------------------------

@app.middleware("http")
async def log_requests(
    request: Request,
    call_next,
):

    start = time.perf_counter()

    correlation_id = str(uuid.uuid4())

    response = await call_next(request)

    latency = (
        time.perf_counter() - start
    ) * 1000

    response.headers[
        "X-Correlation-ID"
    ] = correlation_id

    logger.info(
        f"{request.method} "
        f"{request.url.path} "
        f"{latency:.2f} ms"
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
async def handle_image_error(
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
# Root
# --------------------------------------------------------

@app.get("/")
async def root():

    return {
        "application": "Smart Retail Shelf Monitoring",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# --------------------------------------------------------
# Health
# --------------------------------------------------------

@app.get("/health")
async def health():

    gpu_memory = None

    if torch.cuda.is_available():

        gpu_memory = round(
            torch.cuda.memory_allocated()
            / (1024 ** 2),
            2,
        )

    return {

        "status": "healthy",

        "device": (
            "CUDA"
            if torch.cuda.is_available()
            else "CPU"
        ),

        "model": (
            detector.model_name
            if detector
            else None
        ),

        "gpu_memory_mb": gpu_memory,

    }


# --------------------------------------------------------
# Model Info
# --------------------------------------------------------

@app.get("/model-info")
async def model_info():

    return {

        "model": detector.model_name,

        "framework": "Ultralytics YOLOv11",

        "device": detector.device,

        "confidence_threshold": detector.confidence,

        "iou_threshold": detector.iou,

    }


# --------------------------------------------------------
# Detection Endpoint
# --------------------------------------------------------

@app.post(
    "/api/v1/detect",
    response_model=InferenceResponse,
)
async def detect_objects(
    image: UploadFile = File(...),
):

    if shelf_service is None:

        raise ModelLoadError(
            "ShelfMonitoringService not initialized."
        )

    return await shelf_service.process_image(
        image
    )


# --------------------------------------------------------
# Run
# --------------------------------------------------------

if __name__ == "__main__":

    settings = get_settings()

    import uvicorn

    uvicorn.run(

        "src.main:app",

        host=settings.API_HOST,

        port=settings.API_PORT,

        reload=True,

    )