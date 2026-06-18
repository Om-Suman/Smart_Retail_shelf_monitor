"""
Inventory Counter Service

Aggregates detected objects into an inventory summary.

Responsibilities
----------------
1. Count objects by class.
2. Generate inventory summary.
3. Sort inventory by quantity.

This service has no dependency on YOLO or OpenCV.
"""

from __future__ import annotations

from collections import Counter
from typing import List

from src.models.schemas import (
    BoundingBox,
    InventoryItem,
    InventorySummary,
)


class InventoryCounter:
    """
    Converts object detections into inventory statistics.
    """

    @staticmethod
    def summarize(
        detections: List[BoundingBox],
    ) -> InventorySummary:
        """
        Generate inventory summary from detections.

        Parameters
        ----------
        detections : List[BoundingBox]

        Returns
        -------
        InventorySummary
        """

        counts = Counter(
            detection.class_name
            for detection in detections
        )

        products = [
            InventoryItem(
                product_name=name,
                quantity=quantity,
            )
            for name, quantity in counts.items()
        ]

        # Sort by quantity (highest first)
        products.sort(
            key=lambda product: product.quantity,
            reverse=True,
        )

        return InventorySummary(
            total_objects=len(detections),
            products=products,
        )

    @staticmethod
    def get_product_count(
        detections: List[BoundingBox],
        product_name: str,
    ) -> int:
        """
        Return count of a specific product.

        Parameters
        ----------
        detections : List[BoundingBox]

        product_name : str

        Returns
        -------
        int
        """

        return sum(
            1
            for detection in detections
            if detection.class_name.lower()
            == product_name.lower()
        )

    @staticmethod
    def unique_products(
        detections: List[BoundingBox],
    ) -> List[str]:
        """
        Return unique detected product names.

        Parameters
        ----------
        detections : List[BoundingBox]

        Returns
        -------
        List[str]
        """

        return sorted(
            {
                detection.class_name
                for detection in detections
            }
        )