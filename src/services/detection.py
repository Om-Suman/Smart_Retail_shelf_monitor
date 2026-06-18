"""
YOLOv11 Inference Engine

Responsibilities
----------------
1. Load YOLO model once.
2. Run inference.
3. Convert detections into BoundingBox models.
"""

from __future__ import annotations

import threading
from pathlib import Path
from time import perf_counter
from typing import List, Tuple

import cv2
import numpy as np
import torch
from ultralytics import YOLO

from src.core.config import get_settings
from src.core.exceptions import ModelLoadError
from src.core.logging import logger
from src.models.schemas import BoundingBox


class YOLOInferenceEngine:
    """
    Thread-safe singleton inference engine.
    """

    def __init__(self) -> None:

        settings = get_settings()

        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        self.model_path = settings.MODEL_PATH

        self.confidence = settings.CONF_THRESHOLD

        self.iou = settings.IOU_THRESHOLD

        self.lock = threading.Lock()

        self.model = self._load_model()

    def _load_model(self) -> YOLO:
        """
        Load YOLO model.
        """

        try:

            if not Path(self.model_path).exists():
                logger.warning(
                    "Model file not found locally. "
                    "Ultralytics will download automatically."
                )

            model = YOLO(self.model_path)

            model.to(self.device)

            logger.info(
                f"YOLO loaded on {self.device.upper()}"
            )

            return model

        except Exception as e:

            raise ModelLoadError(
                f"Unable to load model: {e}"
            )

    @property
    def model_name(self) -> str:
        return Path(self.model_path).stem

    def infer(
        self,
        image: np.ndarray,
    ) -> Tuple[List[BoundingBox], float]:
        """
        Run inference.

        Parameters
        ----------
        image

        Returns
        -------
        (
            detections,
            inference_time_ms
        )
        """

        start = perf_counter()

        with self.lock:

            results = self.model.predict(
                source=image,
                conf=self.confidence,
                iou=self.iou,
                verbose=False,
                device=self.device,
            )

        inference_time = (
            perf_counter() - start
        ) * 1000

        detections = self._parse_results(
            results
        )

        return detections, inference_time

    def _parse_results(
        self,
        results,
    ) -> List[BoundingBox]:
        """
        Convert Ultralytics output into
        BoundingBox models.
        """

        parsed: List[BoundingBox] = []

        if len(results) == 0:
            return parsed

        result = results[0]

        names = result.names

        for box in result.boxes:

            cls = int(box.cls.item())

            conf = float(box.conf.item())

            xyxy = (
                box.xyxy[0]
                .cpu()
                .numpy()
                .astype(int)
            )

            parsed.append(

                BoundingBox(

                    class_id=cls,

                    class_name=names[cls],

                    confidence=round(conf, 4),

                    x_min=int(xyxy[0]),

                    y_min=int(xyxy[1]),

                    x_max=int(xyxy[2]),

                    y_max=int(xyxy[3]),
                )

            )

        return parsed

    def warmup(self) -> None:
        """
        Warm up the model.
        """

        dummy = np.zeros(
            (640, 640, 3),
            dtype=np.uint8,
        )

        self.model.predict(
            dummy,
            verbose=False,
            device=self.device,
        )

        logger.info("Model warmup completed.")