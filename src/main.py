"""
FastAPI Entry Point

Responsibilities
----------------
- Initialize application
- Load YOLO model once
- Configure middleware
- Register exception handlers
- Health endpoint
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import torch
from fastapi import FastAPI, Request,UploadFile, File
from fastapi.responses import JSONResponse

from src.utils.image_proc import (
    validate_image_bytes,
    decode_image,
    draw_boxes,
)

from src.core.exceptions import (
    InvalidImageError,
    ModelLoadError,
)
from src.core.logging import logger
from src.services.counter import InventoryCounter
from src.services.detection import YOLOInferenceEngine
from src.services.formatter import ResponseFormatter
from src.models.schemas import InferenceResponse
# ----------------------------------------------------
# Global Services
# ----------------------------------------------------

detector: YOLOInferenceEngine | None = None
counter = InventoryCounter()
formatter = ResponseFormatter()


# ----------------------------------------------------
# Lifespan
# ----------------------------------------------------

@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator:

    global detector

    logger.info("Loading YOLO model...")

    detector = YOLOInferenceEngine()

    detector.warmup()

    logger.info("Application started.")

    yield

    logger.info("Application shutdown.")


# ----------------------------------------------------
# FastAPI App
# ----------------------------------------------------

app = FastAPI(
    title="Smart Retail Shelf Monitoring",
    description="YOLOv11 Inventory Detection API",
    version="1.0.0",
    lifespan=lifespan,
)


# ----------------------------------------------------
# Middleware
# ----------------------------------------------------

@app.middleware("http")
async def request_middleware(
    request: Request,
    call_next,
):

    correlation_id = str(uuid.uuid4())

    start = time.perf_counter()

    response = await call_next(request)

    latency = (time.perf_counter() - start) * 1000

    response.headers["X-Correlation-ID"] = correlation_id

    logger.info(
        f"{request.method} "
        f"{request.url.path} "
        f"{latency:.2f} ms"
    )

    return response


# ----------------------------------------------------
# Exception Handlers
# ----------------------------------------------------

@app.exception_handler(ModelLoadError)
async def model_error(
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
async def image_error(
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
async def generic_error(
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


# ----------------------------------------------------
# Health Check
# ----------------------------------------------------

@app.get("/health")
async def health():

    device = (
        "CUDA"
        if torch.cuda.is_available()
        else "CPU"
    )

    memory = None

    if torch.cuda.is_available():

        memory = round(
            torch.cuda.memory_allocated() / (1024 ** 2),
            2,
        )

    return {
        "status": "healthy",
        "device": device,
        "model": detector.model_name if detector else None,
        "gpu_memory_mb": memory,
    }

# ----------------------------------------------------
# Detection Endpoint
# ----------------------------------------------------

@app.post(
    "/api/v1/detect",
    response_model=InferenceResponse,
)
async def detect_objects(
    image: UploadFile = File(...),
):
    """
    Detect products from an uploaded shelf image.
    """

    if detector is None:
        raise ModelLoadError("Model not initialized.")

    image_bytes = await image.read()

    if not validate_image_bytes(image_bytes):
        raise InvalidImageError(
            "Only JPEG and PNG images are supported."
        )

    image_matrix = decode_image(image_bytes)

    detections, inference_time = detector.infer(
        image_matrix
    )

    annotated = draw_boxes(
        image_matrix,
        detections,
    )

    inventory = counter.summarize(
        detections
    )

    response = formatter.build_response(
        detections=detections,
        inventory=inventory,
        annotated_image=annotated,
        inference_time_ms=inference_time,
        model_name=detector.model_name,
    )

    return response


# ----------------------------------------------------
# Root Endpoint
# ----------------------------------------------------

@app.get("/")
async def root():
    """
    Root endpoint.
    """

    return {
        "application": "Smart Retail Shelf Monitoring",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ----------------------------------------------------
# Run Server
# ----------------------------------------------------

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