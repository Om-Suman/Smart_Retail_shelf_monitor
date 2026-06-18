"""
Utility functions for image validation, preprocessing, annotation,
and encoding.
"""

from __future__ import annotations
import base64

from typing import List, Tuple

import cv2
import numpy as np

from src.models.schemas import BoundingBox

def validate_image_bytes(image_bytes: bytes) -> bool:
    """
    Validate uploaded image by attempting to decode it.
    Compatible with Python 3.13+.
    """

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)

    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    return image is not None


def decode_image(image_bytes: bytes) -> np.ndarray:
    """
    Decode uploaded image bytes into OpenCV image.

    Parameters
    ----------
    image_bytes : bytes

    Returns
    -------
    np.ndarray

    Raises
    ------
    ValueError
        If image decoding fails.
    """

    np_image = np.frombuffer(image_bytes, dtype=np.uint8)

    image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Failed to decode image.")

    return image


def letterbox(
    image: np.ndarray,
    target_size: int = 640,
    color: Tuple[int, int, int] = (114, 114, 114),
) -> Tuple[np.ndarray, float, Tuple[int, int]]:
    """
    Resize image while maintaining aspect ratio using padding.

    Parameters
    ----------
    image : np.ndarray

    target_size : int

    color : tuple

    Returns
    -------
    tuple
        (
            resized_image,
            scaling_factor,
            (pad_x, pad_y)
        )
    """

    h, w = image.shape[:2]

    scale = min(target_size / h, target_size / w)

    new_w = int(round(w * scale))
    new_h = int(round(h * scale))

    resized = cv2.resize(
        image,
        (new_w, new_h),
        interpolation=cv2.INTER_LINEAR,
    )

    canvas = np.full(
        (target_size, target_size, 3),
        color,
        dtype=np.uint8,
    )

    pad_x = (target_size - new_w) // 2
    pad_y = (target_size - new_h) // 2

    canvas[
        pad_y : pad_y + new_h,
        pad_x : pad_x + new_w,
    ] = resized

    return canvas, scale, (pad_x, pad_y)


def draw_boxes(
    image: np.ndarray,
    detections: List[BoundingBox],
) -> np.ndarray:
    """
    Draw bounding boxes and labels.

    Parameters
    ----------
    image : np.ndarray

    detections : List[BoundingBox]

    Returns
    -------
    np.ndarray
    """

    annotated = image.copy()

    for det in detections:

        x1 = det.x_min
        y1 = det.y_min
        x2 = det.x_max
        y2 = det.y_max

        label = (
            f"{det.class_name} "
            f"{det.confidence:.2f}"
        )

        cv2.rectangle(
            annotated,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2,
        )

        (text_w, text_h), _ = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            2,
        )

        cv2.rectangle(
            annotated,
            (x1, y1 - text_h - 10),
            (x1 + text_w + 6, y1),
            (0, 255, 0),
            -1,
        )

        cv2.putText(
            annotated,
            label,
            (x1 + 3, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )

    return annotated


def image_to_base64(image: np.ndarray) -> str:
    """
    Convert OpenCV image into Base64 string.

    Parameters
    ----------
    image : np.ndarray

    Returns
    -------
    str
    """

    success, buffer = cv2.imencode(".jpg", image)

    if not success:
        raise ValueError("Failed to encode image.")

    return base64.b64encode(buffer).decode("utf-8")


def base64_to_image(encoded: str) -> np.ndarray:
    """
    Convert Base64 string back into OpenCV image.

    Parameters
    ----------
    encoded : str

    Returns
    -------
    np.ndarray
    """

    image_bytes = base64.b64decode(encoded)

    image_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8,
    )

    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR,
    )

    if image is None:
        raise ValueError("Failed to decode Base64 image.")

    return image