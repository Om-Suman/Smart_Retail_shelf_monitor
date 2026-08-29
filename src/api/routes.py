from __future__ import annotations

import torch
from fastapi import APIRouter, Depends, File, UploadFile

from src.api.dependencies import get_detector, get_shelf_service
from src.core.exceptions import ModelLoadError
from src.models.schemas import InferenceResponse
from src.services.detection import MultiModelInferenceEngine
from src.services.shelf_service import ShelfMonitoringService

router = APIRouter()


@router.get(
    "/",
    tags=["General"],
)
async def root() -> dict[str, str]:
    return {
        "application": "Smart Retail Shelf Monitoring",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@router.get(
    "/health",
    tags=["Health"],
)
async def health(
    detector: MultiModelInferenceEngine = Depends(get_detector),
) -> dict[str, str | float | list[str] | None]:
    gpu_memory = None

    if torch.cuda.is_available():
        gpu_memory = round(torch.cuda.memory_allocated() / (1024**2), 2)

    return {
        "status": "healthy",
        "device": detector.device.upper(),
        "models": ["product_best", "void_best"],
        "gpu_memory_mb": gpu_memory,
    }


@router.get(
    "/model-info",
    tags=["Model"],
)
async def model_info(
    detector: MultiModelInferenceEngine = Depends(get_detector),
) -> dict[str, str | float | list[str]]:
    return {
        "models": ["product_best", "void_best"],
        "framework": "Ultralytics YOLOv11",
        "device": detector.device,
        "confidence_threshold": detector.confidence,
        "iou_threshold": detector.iou,
    }


@router.post(
    "/api/v1/detect",
    response_model=InferenceResponse,
    tags=["Detection"],
)
async def detect_objects(
    image: UploadFile = File(...),
    shelf_service: ShelfMonitoringService = Depends(get_shelf_service),
) -> InferenceResponse:
    if shelf_service is None:
        raise ModelLoadError("ShelfMonitoringService not initialized.")

    return await shelf_service.process_image(image)
