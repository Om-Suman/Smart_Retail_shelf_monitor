from __future__ import annotations

import numpy as np

from src.models.schemas import BoundingBox, DetectionMetadata, InferenceResponse, InventorySummary
from src.utils.image_proc import image_to_base64


class ResponseFormatter:
    @staticmethod
    def build_response(
        *,
        detections: list[BoundingBox],
        inventory: InventorySummary,
        annotated_image: np.ndarray,
        inference_time_ms: float,
        model_name: str,
    ) -> InferenceResponse:
        height, width = annotated_image.shape[:2]

        metadata = DetectionMetadata(
            inference_time_ms=round(inference_time_ms, 2),
            image_width=width,
            image_height=height,
            model_name=model_name,
        )

        return InferenceResponse(
            success=True,
            detections=detections,
            inventory=inventory,
            annotated_image=image_to_base64(annotated_image),
            metadata=metadata,
        )

    @staticmethod
    def build_error_response(message: str) -> dict[str, bool | str]:
        return {
            "success": False,
            "error": message,
        }
