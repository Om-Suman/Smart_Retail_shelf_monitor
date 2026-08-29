from __future__ import annotations

from fastapi import UploadFile

from src.core.exceptions import InvalidImageError
from src.models.schemas import InferenceResponse
from src.services.counter import InventoryCounter
from src.services.detection import MultiModelInferenceEngine
from src.services.formatter import ResponseFormatter
from src.utils.image_proc import decode_image, draw_boxes, validate_image_bytes


class ShelfMonitoringService:
    def __init__(
        self,
        detector: MultiModelInferenceEngine,
    ) -> None:
        self.detector = detector
        self.counter = InventoryCounter()
        self.formatter = ResponseFormatter()

    async def process_image(
        self,
        image: UploadFile,
    ) -> InferenceResponse:
        image_bytes = await image.read()

        if not validate_image_bytes(image_bytes):
            raise InvalidImageError("Invalid image. Upload JPEG or PNG.")

        image_matrix = decode_image(image_bytes)
        
        # Run inference with both models
        product_detections, void_detections, product_time, void_time = self.detector.infer(image_matrix)
        
        # Combine detections from both models
        all_detections = product_detections + void_detections
        
        # Create annotated image with detections from both models
        annotated_image = draw_boxes(image_matrix, all_detections)
        
        # Calculate inventory based on all detections
        inventory = self.counter.summarize(all_detections)

        return self.formatter.build_response(
            detections=all_detections,
            inventory=inventory,
            annotated_image=annotated_image,
            product_inference_time_ms=product_time,
            void_inference_time_ms=void_time,
            model_names=["product_best", "void_best"],
        )
