"""
API Routes

Defines all REST endpoints for the Smart Retail Shelf Monitoring API.
"""

from __future__ import annotations

import torch

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
)

from src.api.dependencies import (
    get_detector,
    get_shelf_service,
)

from src.core.exceptions import (
    ModelLoadError,
)

from src.models.schemas import (
    InferenceResponse,
)

from src.services.detection import (
    YOLOInferenceEngine,
)

from src.services.shelf_service import (
    ShelfMonitoringService,
)

router = APIRouter()


# --------------------------------------------------------
# Root Endpoint
# --------------------------------------------------------

@router.get(
    "/",
    tags=["General"],
)
async def root():

    return {
        "application": "Smart Retail Shelf Monitoring",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# --------------------------------------------------------
# Health Endpoint
# --------------------------------------------------------

@router.get(
    "/health",
    tags=["Health"],
)
async def health(
    detector: YOLOInferenceEngine = Depends(
        get_detector
    ),
):

    gpu_memory = None

    if torch.cuda.is_available():

        gpu_memory = round(
            torch.cuda.memory_allocated()
            / (1024 ** 2),
            2,
        )

    return {

        "status": "healthy",

        "device": detector.device.upper(),

        "model": detector.model_name,

        "gpu_memory_mb": gpu_memory,

    }


# --------------------------------------------------------
# Model Information
# --------------------------------------------------------

@router.get(
    "/model-info",
    tags=["Model"],
)
async def model_info(
    detector: YOLOInferenceEngine = Depends(
        get_detector
    ),
):

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

@router.post(
    "/api/v1/detect",
    response_model=InferenceResponse,
    tags=["Detection"],
)
async def detect_objects(
    image: UploadFile = File(...),
    shelf_service: ShelfMonitoringService = Depends(
        get_shelf_service
    ),
):

    if shelf_service is None:

        raise ModelLoadError(
            "ShelfMonitoringService not initialized."
        )

    return await shelf_service.process_image(
        image
    )