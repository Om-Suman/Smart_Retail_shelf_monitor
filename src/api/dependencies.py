from __future__ import annotations

from src.services.detection import MultiModelInferenceEngine
from src.services.shelf_service import ShelfMonitoringService

_detector: MultiModelInferenceEngine | None = None
_service: ShelfMonitoringService | None = None


def initialize_services() -> None:
    global _detector
    global _service

    if _detector is None:
        _detector = MultiModelInferenceEngine()
        _detector.warmup()

    if _service is None:
        _service = ShelfMonitoringService(_detector)


def get_detector() -> MultiModelInferenceEngine:
    if _detector is None:
        raise RuntimeError("Detector has not been initialized.")

    return _detector


def get_shelf_service() -> ShelfMonitoringService:
    if _service is None:
        raise RuntimeError("ShelfMonitoringService has not been initialized.")

    return _service
