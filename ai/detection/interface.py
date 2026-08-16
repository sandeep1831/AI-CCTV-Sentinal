"""AI-CCTV Sentinel — Detector interface (Layer 4: Detection).

Any detector (YOLO26n today, a different architecture later) must
satisfy this contract. Nothing downstream (tracking, risk, alerts,
backend) may depend on Ultralytics/YOLO directly — only on this
interface and the `Detection` schema it returns. This is the
replaceability requirement from Task 2 §50.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from backend.schemas.detection import Detection


class Detector(ABC):
    """Contract for any object detector used in the pipeline."""

    @abstractmethod
    def load(self) -> None:
        """Load model weights (see configs/model.yaml `detector.weights`)."""

    @abstractmethod
    def predict(self, camera_id: str, frame_id: int, image: np.ndarray) -> list[Detection]:
        """Run inference on a single frame and return zero or more Detections."""

    @abstractmethod
    def warmup(self) -> None:
        """Run a throwaway inference pass to avoid a cold-start penalty
        on the first real frame."""
