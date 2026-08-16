"""AI-CCTV Sentinel — scripts/specialists/specialist_inference.py (Task 6 §61-62).

Common inference interface for both specialist branches:

    specialist_result = specialist.predict(animal="snake", crop=image_crop, source_detection_id="DET-1")
    specialist_result = specialist.predict(animal="dog", crop=dog_crop, source_detection_id="DET-2")

Returns a validated backend.schemas.specialist.SpecialistResult. If
any required field cannot be populated (e.g. a specialist model isn't
loaded/trained yet), returns a result with specialist_status="invalid"
rather than silently continuing (Task 6 §62) or crashing the caller.

This module is import-only (no CLI) — it's the interface Task 7+ and
later integration tasks will call into.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.schemas.specialist import (  # noqa: E402
    DogHealthCategory,
    Region,
    SnakeCategory,
    SpecialistResult,
    SpecialistStatus,
    SpecialistType,
    Visibility,
)

SNAKE_MODEL_PATH = Path("models/specialists/snake/sentinel-snake-cls-v1.0.0.pt")
DOG_HEALTH_MODEL_PATH = Path("models/specialists/dog_health/sentinel-dog-health-v1.0.0.pt")


class SpecialistUnavailableError(RuntimeError):
    """Raised when a specialist model hasn't been trained/registered yet."""


class SpecialistPipeline:
    """Loads (lazily) and serves both specialist branches through one interface."""

    def __init__(self) -> None:
        self._snake_model = None
        self._dog_health_model = None

    def _load_snake_model(self):
        if self._snake_model is None:
            if not SNAKE_MODEL_PATH.exists():
                raise SpecialistUnavailableError(
                    f"Snake specialist model not found at {SNAKE_MODEL_PATH}. "
                    "Train and register it first (train_snake_classifier.py + "
                    "save into models/specialists/snake/)."
                )
            from ultralytics import YOLO

            self._snake_model = YOLO(str(SNAKE_MODEL_PATH))
        return self._snake_model

    def _load_dog_health_model(self):
        if self._dog_health_model is None:
            if not DOG_HEALTH_MODEL_PATH.exists():
                raise SpecialistUnavailableError(
                    f"Dog health specialist model not found at {DOG_HEALTH_MODEL_PATH}. "
                    "This is EXPECTED if Task 6 §52's data-sufficiency gate has not "
                    "yet been satisfied — see docs/research/task6 status."
                )
            from ultralytics import YOLO

            self._dog_health_model = YOLO(str(DOG_HEALTH_MODEL_PATH))
        return self._dog_health_model

    def predict(
        self,
        *,
        animal: str,
        crop: np.ndarray,
        source_detection_id: str,
        visibility: Visibility = Visibility.SUFFICIENT,
        unknown_threshold: float = 0.60,
    ) -> SpecialistResult:
        """Route to the correct specialist branch and return a validated result.

        On any failure to obtain a real model prediction, returns a
        specialist_status="invalid" result rather than fabricating one.
        """

        timestamp = datetime.now(timezone.utc)

        try:
            if animal == "snake":
                return self._predict_snake(crop, source_detection_id, timestamp, unknown_threshold)
            if animal == "dog":
                return self._predict_dog_health(crop, source_detection_id, timestamp, visibility)
            raise ValueError(f"Unsupported animal for specialist inference: {animal}")
        except SpecialistUnavailableError as exc:
            return self._invalid_result(animal, source_detection_id, timestamp, reason=str(exc))

    def _predict_snake(self, crop, source_detection_id, timestamp, unknown_threshold) -> SpecialistResult:
        model = self._load_snake_model()
        results = model.predict(source=crop, verbose=False)
        probs = results[0].probs
        top1_idx = int(probs.top1)
        top1_conf = float(probs.top1conf)
        class_name = results[0].names[top1_idx]

        prediction = class_name if top1_conf >= unknown_threshold else SnakeCategory.UNKNOWN.value

        return SpecialistResult.build(
            animal="snake",
            specialist_type=SpecialistType.SNAKE_CLASSIFICATION,
            prediction=prediction,
            confidence=top1_conf,
            visibility=Visibility.SUFFICIENT,
            source_detection_id=source_detection_id,
            model_version="snake-cls-v1.0.0",
            timestamp=timestamp,
        )

    def _predict_dog_health(self, crop, source_detection_id, timestamp, visibility) -> SpecialistResult:
        if visibility == Visibility.INSUFFICIENT_VISIBILITY:
            # Visibility policy override (Task 6 §31) — never even
            # calls the classifier when visibility is insufficient.
            return SpecialistResult.build(
                animal="dog",
                specialist_type=SpecialistType.VISIBLE_HEALTH_SCREENING,
                prediction=DogHealthCategory.UNABLE_TO_ASSESS.value,
                confidence=1.0,
                visibility=visibility,
                source_detection_id=source_detection_id,
                model_version="dog-health-v1.0.0",
                timestamp=timestamp,
            )

        model = self._load_dog_health_model()
        results = model.predict(source=crop, verbose=False)
        probs = results[0].probs
        top1_idx = int(probs.top1)
        top1_conf = float(probs.top1conf)
        class_name = results[0].names[top1_idx]

        return SpecialistResult.build(
            animal="dog",
            specialist_type=SpecialistType.VISIBLE_HEALTH_SCREENING,
            prediction=class_name,
            confidence=top1_conf,
            visibility=visibility,
            source_detection_id=source_detection_id,
            model_version="dog-health-v1.0.0",
            timestamp=timestamp,
        )

    @staticmethod
    def _invalid_result(animal, source_detection_id, timestamp, reason: str) -> SpecialistResult:
        specialist_type = (
            SpecialistType.SNAKE_CLASSIFICATION if animal == "snake" else SpecialistType.VISIBLE_HEALTH_SCREENING
        )
        return SpecialistResult(
            animal=animal,
            specialist_type=specialist_type,
            prediction="unknown" if animal == "snake" else "unable_to_assess",
            confidence=0.0,
            visibility=Visibility.INSUFFICIENT_VISIBILITY,
            source_detection_id=source_detection_id,
            model_version="unavailable",
            timestamp=timestamp,
            specialist_status=SpecialistStatus.INVALID,
        )


if __name__ == "__main__":
    # Lightweight self-check: confirm both branches return a graceful
    # invalid result when no model is registered yet — never a crash,
    # never a fabricated confident prediction.
    pipeline = SpecialistPipeline()
    dummy_crop = np.zeros((224, 224, 3), dtype=np.uint8)

    snake_result = pipeline.predict(animal="snake", crop=dummy_crop, source_detection_id="DET-TEST-1")
    print("Snake specialist (no model registered yet):")
    print(f"  status={snake_result.specialist_status}, prediction={snake_result.prediction}")

    dog_result = pipeline.predict(animal="dog", crop=dummy_crop, source_detection_id="DET-TEST-2")
    print("Dog health specialist (no model registered yet):")
    print(f"  status={dog_result.specialist_status}, prediction={dog_result.prediction}")
