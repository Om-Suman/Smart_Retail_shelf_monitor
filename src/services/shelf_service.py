"""
Shelf Monitoring Service

Coordinates the complete Computer Vision pipeline.

Pipeline
--------
UploadFile
    ↓
Validate Image
    ↓
Decode Image
    ↓
YOLO Detection
    ↓
Draw Bounding Boxes
    ↓
Inventory Counter
    ↓
Response Formatter
"""

from __future__ import annotations

from fastapi import UploadFile

from src.core.exceptions import InvalidImageError
from src.services.counter import InventoryCounter
from src.services.detection import YOLOInferenceEngine
from src.services.formatter import ResponseFormatter
from src.utils.image_proc import (
    decode_image,
    draw_boxes,
    validate_image_bytes,
)


class ShelfMonitoringService:
    """
    Orchestrates the complete shelf monitoring pipeline.
    """

    def __init__(
        self,
        detector: YOLOInferenceEngine,
    ) -> None:

        self.detector = detector
        self.counter = InventoryCounter()
        self.formatter = ResponseFormatter()

    async def process_image(
        self,
        image: UploadFile,
    ):
        """
        Process uploaded shelf image.

        Parameters
        ----------
        image : UploadFile

        Returns
        -------
        InferenceResponse
        """

        image_bytes = await image.read()

        if not validate_image_bytes(image_bytes):
            raise InvalidImageError(
                "Invalid image. Upload JPEG or PNG."
            )

        image_matrix = decode_image(image_bytes)

        detections, inference_time = self.detector.infer(
            image_matrix
        )

        annotated_image = draw_boxes(
            image_matrix,
            detections,
        )

        inventory = self.counter.summarize(
            detections
        )

        return self.formatter.build_response(
            detections=detections,
            inventory=inventory,
            annotated_image=annotated_image,
            inference_time_ms=inference_time,
            model_name=self.detector.model_name,
        )