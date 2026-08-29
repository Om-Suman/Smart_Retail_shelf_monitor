from typing import List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """
    Represents a single detected object.
    """
    class_id: int = Field(..., ge=0)
    class_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)

    x_min: int
    y_min: int
    x_max: int
    y_max: int
    model_source: str = Field(default="product")  # product or void


class InventoryItem(BaseModel):
    """
    Inventory information for a single product.
    """

    product_name: str
    quantity: int = Field(..., ge=0)


class InventorySummary(BaseModel):
    """
    Complete inventory summary.
    """

    total_objects: int
    products: List[InventoryItem]


class DetectionMetadata(BaseModel):
    """
    Metadata about the inference.
    """

    inference_time_ms: float
    image_width: int
    image_height: int
    model_names: List[str]  # e.g., ["product_best", "void_best"]
    model_times_ms: dict  # e.g., {"product_best": 100.5, "void_best": 95.3}


class InferenceResponse(BaseModel):
    """
    Final API response.
    """
    success: bool
    detections: List[BoundingBox]
    inventory: InventorySummary
    annotated_image: str
    metadata: Optional[DetectionMetadata] = None