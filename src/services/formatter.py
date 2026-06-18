"""
Formatter Service

Creates the final API response returned by FastAPI.

Responsibilities
----------------
1. Build metadata.
2. Encode annotated image.
3. Construct the InferenceResponse model.
"""

from __future__ import annotations

from typing import List

import numpy as np

from src.models.schemas import (
    BoundingBox,
    DetectionMetadata,
    InferenceResponse,
    InventorySummary,
)
from src.utils.image_proc import image_to_base64


class ResponseFormatter:
    """
    Formats inference results into the API response schema.
    """

    @staticmethod
    def build_response(
        *,
        detections: List[BoundingBox],
        inventory: InventorySummary,
        annotated_image: np.ndarray,
        inference_time_ms: float,
        model_name: str,
    ) -> InferenceResponse:
        """
        Build the final API response.

        Parameters
        ----------
        detections : List[BoundingBox]

        inventory : InventorySummary

        annotated_image : np.ndarray

        inference_time_ms : float

        model_name : str

        Returns
        -------
        InferenceResponse
        """

        height, width = annotated_image.shape[:2]

        metadata = DetectionMetadata(
            inference_time_ms=round(
                inference_time_ms,
                2,
            ),
            image_width=width,
            image_height=height,
            model_name=model_name,
        )

        encoded_image = image_to_base64(
            annotated_image
        )

        return InferenceResponse(
            success=True,
            detections=detections,
            inventory=inventory,
            annotated_image=encoded_image,
            metadata=metadata,
        )

    @staticmethod
    def build_error_response(
        message: str,
    ) -> dict:
        """
        Standard error response.

        Parameters
        ----------
        message : str

        Returns
        -------
        dict
        """

        return {
            "success": False,
            "error": message,
        }