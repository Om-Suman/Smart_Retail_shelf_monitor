from __future__ import annotations

from src.services.detection import YOLOInferenceEngine
from src.services.shelf_service import ShelfMonitoringService

_detector: YOLOInferenceEngine | None = None
_service: ShelfMonitoringService | None = None


def initialize_services() -> None:
    global _detector
    global _service

    if _detector is None:
        _detector = YOLOInferenceEngine()
        _detector.warmup()

    if _service is None:
        _service = ShelfMonitoringService(_detector)


def get_detector() -> YOLOInferenceEngine:
    if _detector is None:
        raise RuntimeError("Detector has not been initialized.")

    return _detector


def get_shelf_service() -> ShelfMonitoringService:
    if _service is None:
        raise RuntimeError("ShelfMonitoringService has not been initialized.")

    return _service
